from __future__ import annotations
from typing import Callable, Dict, Any, Optional
import os, json, shlex, subprocess, tempfile, uuid, requests, re

from javu_agi.tools.adapters.web_adapter import WebAdapter
from javu_agi.tools.adapters.storage_adapter import StorageAdapter
from javu_agi.tools.adapters.telegram_adapter import TelegramAdapter
from javu_agi.tools.adapters.discord_adapter import DiscordAdapter
from javu_agi.tools.adapters.slack_adapter import SlackAdapter
from javu_agi.tools.adapters.github_adapter import GitHubAdapter
from javu_agi.tools.adapters.gmail_adapter import GmailAdapter
from javu_agi.tools.adapters.gcal_adapter import GCalAdapter
from javu_agi.tools.adapters.gdrive_adapter import GDriveAdapter
from javu_agi.tools.adapters.gcontacts_adapter import GContactsAdapter
from javu_agi.tools.adapters.ms_graph_mail_adapter import MSGraphMailAdapter
from javu_agi.tools.adapters.ms_graph_calendar_adapter import MSGraphCalendarAdapter
from javu_agi.tools.adapters.ms_graph_files_adapter import MSGraphFilesAdapter
from javu_agi.tools.adapters.ms_graph_teams_adapter import MSGraphTeamsAdapter
from javu_agi.tools.adapters.notion_adapter import NotionAdapter
from javu_agi.tools.adapters.canva_proxy_adapter import CanvaProxyAdapter
from javu_agi.config import (
    load_policy,
    load_permissions,
    load_models_cfg,
    load_router_policy,
)

POLICY = load_policy()
PERMISSIONS = load_permissions()
MODELS = load_models_cfg()
ROUTER = load_router_policy()

__all__ = ["ToolRegistry", "ToolError"]


class ToolError(Exception):
    pass


# ==== HARD LIMITS & POLICIES (mirror worker) ====
ALLOW_CMDS = {"python", "jq"}  # deny-by-default
DENY_CHARS = set("`$(){}[]|;&><\\")  # metashell chars disallowed
DENY_PATTERNS = [
    r"\b(rm\s+-rf|mkfs|mount|umount|shutdown|reboot|halt)\b",
    r"/etc/passwd|/etc/shadow",
    r"ssh\s+|scp\s+|sftp\s+|curl\s+|wget\s+|http[s]?://",
]
MAX_REMOTE_INPUT = 32_000  # bytes
MAX_REMOTE_CMD = 8_000  # chars
MAX_LOCAL_OUT = 64_000  # bytes
DEFAULT_TIMEOUT = 8  # seconds

_DENY_RE = [re.compile(p, re.I) for p in DENY_PATTERNS]


def _bad_chars(s: str) -> Optional[str]:
    bad = [c for c in s if c in DENY_CHARS]
    return "".join(sorted(set(bad))) if bad else None


def _validate_cmd(cmd: str):
    if not isinstance(cmd, str) or not cmd.strip():
        raise ToolError("empty command")
    if len(cmd) > MAX_REMOTE_CMD:
        raise ToolError("command too long")
    bc = _bad_chars(cmd)
    if bc:
        raise ToolError(f"forbidden shell meta-chars: {bc}")
    for rx in _DENY_RE:
        if rx.search(cmd):
            raise ToolError("denied pattern in command")
    parts = shlex.split(cmd)
    if not parts:
        raise ToolError("cannot parse command")
    if parts[0] not in ALLOW_CMDS:
        raise ToolError(f"tool not allowed: {parts[0]}")
    return parts


class ToolRegistry:
    """
    Registry fungsi tool (pure-Python) + gateway aman ke worker sandbox (HTTP).
    - Local tools: hanya fungsi Python yang kita daftarkan (tidak ada shell).
    - Remote tools: perintah dikirim ke service worker (/run), dengan policy & limit.
    """

    def __init__(self):
        self._tools: Dict[str, Callable[[Dict[str, Any]], Dict[str, Any]]] = {}
        self._allow_cmds = set(ALLOW_CMDS)  # local allow
        self.default_timeout = int(os.getenv("TOOL_TIMEOUT", str(DEFAULT_TIMEOUT)))
        self.remote_url = os.environ.get(
            "TOOL_WORKER_URL"
        )  # e.g. http://tool-worker:9090
        self._http = requests.Session() if self.remote_url else None

    # ===== registry (pure-python) =====
    def register(self, name: str, fn: Callable[[Dict[str, Any]], Dict[str, Any]]):
        if not callable(fn):
            raise ToolError("fn must be callable")
        self._tools[name] = fn

    def list(self):
        return sorted(self._tools.keys())

    def run(self, name: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        fn = self._tools.get(name)
        if not fn:
            raise ToolError(f"unknown tool: {name}")
        try:
            return fn(payload or {})
        except ToolError:
            raise
        except Exception as e:
            return {"error": f"{type(e).__name__}: {e}"}

    # ===== local sandboxed command helper (no shell) =====
    def _exec_cmd(
        self, cmd: str, input_text: Optional[str] = None, timeout: Optional[int] = None
    ) -> Dict[str, Any]:
        parts = _validate_cmd(cmd)  # reuse same hard validation
        if parts[0] not in self._allow_cmds:
            raise ToolError(f"command not allowed locally: {parts[0]}")
        try:
            p = subprocess.Popen(
                parts,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env={
                    "PATH": "/usr/bin:/bin",
                    "LC_ALL": "C",
                    "LANG": "C",
                    "NO_COLOR": "1",
                },
            )
            out, err = p.communicate(
                input=(input_text.encode("utf-8") if input_text else None),
                timeout=timeout or self.default_timeout,
            )
            out, err = out[:MAX_LOCAL_OUT], err[:MAX_LOCAL_OUT]
            return {
                "code": p.returncode,
                "stdout": out.decode("utf-8", "ignore"),
                "stderr": err.decode("utf-8", "ignore"),
            }
        except subprocess.TimeoutExpired:
            try:
                p.kill()
            except Exception:
                pass
            return {"code": 124, "stdout": "", "stderr": "timeout"}

    # ===== remote worker dispatch (HTTP) =====
    def run_remote(self, cmd: str, input_text: Optional[str] = None) -> Dict[str, Any]:
        if not self.remote_url or not self._http:
            raise ToolError("remote worker not configured")
        _validate_cmd(cmd)  # enforce same policy before sending
        if input_text and len(input_text.encode("utf-8")) > MAX_REMOTE_INPUT:
            raise ToolError("input too large")
        try:
            r = self._http.post(
                self.remote_url.rstrip("/") + "/run",
                json={"cmd": cmd, "input_text": input_text},
                timeout=min(12, self.default_timeout + 4),
            )
            r.raise_for_status()
            data = r.json()
            # normalize fields
            return {
                "code": int(data.get("code", -1)),
                "stdout": str(data.get("stdout", ""))[:MAX_LOCAL_OUT],
                "stderr": str(data.get("stderr", ""))[:MAX_LOCAL_OUT],
            }
        except requests.RequestException as e:
            raise ToolError(f"worker error: {e}") from e

    # ===== built-in pure-python tools (aman) =====
    def register_builtin(self):
        # JSON transformer (tanpa dependensi eksternal; mini jq fallback)
        def json_filter(payload: Dict[str, Any]) -> Dict[str, Any]:
            data = payload.get("data")
            if data is None:
                return {"error": "no data"}
            # expr diabaikan di fallback ini (kita bisa tambah mini-selector sederhana)
            try:
                json.dumps(data)  # validate serializable
                return {"result": data}
            except Exception as e:
                return {"error": f"invalid json: {e}"}

        self.register("json_filter", json_filter)

        # Python inline minimal (ditulis ke file tmp; dieksekusi via _exec_cmd tanpa shell)
        def python_inline(payload: Dict[str, Any]) -> Dict[str, Any]:
            code = payload.get("code", "")
            if not isinstance(code, str) or not code.strip():
                return {"error": "empty code"}
            # tulis file tmp
            path = os.path.join(tempfile.gettempdir(), f"tool_{uuid.uuid4().hex}.py")
            try:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(code)
                res = self._exec_cmd(
                    f"python {shlex.quote(path)}", timeout=min(self.default_timeout, 10)
                )
                return res
            finally:
                try:
                    os.remove(path)
                except Exception:
                    pass

        self.register("python_inline", python_inline)

        # Ringkasan teks ultra-sederhana (pure python, aman)
        def summarize(payload: Dict[str, Any]) -> Dict[str, Any]:
            text = str(payload.get("text", ""))
            n = int(payload.get("max_sentences", 2))
            if not text.strip():
                return {"summary": ""}
            sents = [s.strip() for s in re.split(r"[.!?]\s+", text) if s.strip()]
            return {"summary": ". ".join(sents[: max(1, n)])}

        self.register("summarize", summarize)

    def register_integrations(self):
        web = WebAdapter()
        store = StorageAdapter()
        tg = TelegramAdapter()
        dc = DiscordAdapter()
        sk = SlackAdapter()
        gh = GitHubAdapter()
        gm = GmailAdapter()
        gc = GCalAdapter()
        gd = GDriveAdapter()
        gco = GContactsAdapter()
        msm = MSGraphMailAdapter()
        msc = MSGraphCalendarAdapter()
        msf = MSGraphFilesAdapter()
        mst = MSGraphTeamsAdapter()
        notion = NotionAdapter()
        canva = CanvaProxyAdapter()

        self.register("web.get", web.get)
        self.register("web.head", web.head)
        self.register("storage.put_text", store.put_text)
        self.register("storage.get_text", store.get_text)
        self.register("telegram.send", tg.send)
        self.register("telegram.get_updates", tg.get_updates)
        self.register("discord.post", dc.post)
        self.register("discord.fetch", dc.fetch)
        self.register("slack.post_message", sk.post_message)
        self.register("slack.list_messages", sl.list_messages)
        self.register("github.create_issue", gh.create_issue)
        # Gmail
        self.register("gmail.list_messages", gm.list_messages)
        self.register("gmail.get_message", gm.get_message)
        self.register("gmail.send", gm.send)
        self.register("gmail.list_threads", gm.list_threads)
        self.register("gmail.draft", gm.draft)
        # Google Calendar
        self.register("gcal.list_events", gc.list_events)
        self.register("gcal.create_event", gc.create_event)
        # Google Drive & Contacts
        self.register("gdrive.list_files", gd.list_files)
        self.register("gdrive.download_file", gd.download_file)
        self.register("gdrive.upload_text", gd.upload_text)
        self.register("gcontacts.list", gco.list)
        # Microsoft Graph
        self.register("ms.mail.list_messages", msm.list_messages)
        self.register("ms.mail.send", msm.send)
        self.register("ms.calendar.list_events", msc.list_events)
        self.register("ms.calendar.create_event", msc.create_event)
        self.register("ms.files.list_root", msf.list_root)
        self.register("ms.files.download", msf.download)
        self.register("ms.files.upload_text", msf.upload_text)
        self.register("ms.teams.post_message", mst.post_message)
        self.register("ms.teams.list_messages", mst.list_messages)
        # MS Graph Files – SharePoint site
        self.register("ms.files.list_site_drive", msf.list_site_drive)
        # Notion
        self.register("notion.search", notion.search)
        self.register("notion.create_page", notion.create_page)
        # Canva via Proxy
        self.register("canva.create_design", canva.create_design)
        self.register("canva.publish", canva.publish)
        self.register("canva.list_designs", canva.list_designs)

    # === PATCH: deny call bernuansa training/distill lewat remote cmd ===
    _FORBIDDEN_WORDS = {
        "train",
        "fine-tune",
        "finetune",
        "distill",
        "pretrain",
        "sft",
        "dpo",
        "ppo",
    }

    _old_run_remote = getattr(ToolRegistry, "run_remote", None)

    def _guarded_run_remote(self, cmd: str, input_text: str | None = None):
        lower = (cmd or "").lower()
        if any(w in lower for w in _FORBIDDEN_WORDS):
            raise ToolError("blocked: training/distillation commands are disabled")
        return _old_run_remote(self, cmd, input_text)

    if _old_run_remote:
        ToolRegistry.run_remote = _guarded_run_remote
