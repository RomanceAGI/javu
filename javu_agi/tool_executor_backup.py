from __future__ import annotations
import yaml
import os
import json
import re
import time
import traceback
import multiprocessing as mp
import subprocess
import jsonschema
from pathlib import Path
from typing import Callable, Dict, List, Any, Optional

from javu_agi.llm import call_llm
from javu_agi.utils.logger import log_user
from javu_agi.tools.tool_contracts import default_contracts, enforce_contracts

# Policy, Limits, Audit, RateLimit
_DEFAULT_TIMEOUT_S = int(os.getenv("TOOL_TIMEOUT_S", "30"))
_ALLOWED = {t.strip() for t in os.getenv("ALLOWED_TOOLS", "").split(",") if t.strip()}
_GITHUB_ENABLED = os.getenv("GITHUB_PUSH_ENABLED", "false").lower() in {
    "1",
    "true",
    "yes",
}

_PERM_FILE = os.getenv("TOOL_PERMISSIONS", "javu_agi/tools/permissions.yaml")
_AUDIT_DIR = os.getenv("TOOL_AUDIT_DIR", "logs/tool_audit")
Path(_AUDIT_DIR).mkdir(parents=True, exist_ok=True)

MANIFEST = yaml.safe_load(open(Path("tools/tool_manifest.yaml")))
ALLOW = {t["name"]: t for t in MANIFEST["allowed"]}
BLOCK = set(MANIFEST.get("blocked", []))

# Note: Contract enforcement happens within the main tool_executor module.  This
# backup file should not evaluate contracts at import time because the
# variables `tool` and `input_text` are undefined in this context.  Any such
# checks would raise a NameError on import.  Therefore, contract enforcement
# has been deliberately removed here.


def execute(tool_name, args):
    """
    Legacy executor for validating tool arguments.

    This function performs basic allowlist and block checks, then validates the
    provided arguments against the declared JSON schema in the tool manifest.
    It does not actually run the tool.  Use ``execute_tool`` for invocation.
    """
    if tool_name in BLOCK:
        raise PermissionError("Tool blocked by policy")
    meta = ALLOW.get(tool_name)
    if not meta:
        raise PermissionError("Tool not allowlisted")
    # validate args against a simple JSON schema where all values are strings
    schema = {
        "type": "object",
        "properties": {k: {"type": "string"} for k in meta.get("args_schema", {})},
        "additionalProperties": False,
    }
    jsonschema.validate(args, schema)
    # no return value; validation passes silently
    return None


def _audit(entry: Dict[str, Any]):
    """Write one audit record (JSON) per tool invocation/decision."""
    p = Path(_AUDIT_DIR) / f"{int(time.time()*1000)}.json"
    try:
        p.write_text(json.dumps(entry, ensure_ascii=False))
    except Exception:
        pass


def _load_yaml(path: str) -> Dict[str, Any]:
    try:
        import yaml

        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except Exception:
        return {}


_PERM = _load_yaml(_PERM_FILE)

try:
    _PERM = yaml.safe_load(Path("javu_agi/tools/permissions.yaml").read_text()) or {}
except Exception:
    _PERM = {"tools": {}}

AUDIT_PATH = os.getenv("TOOLS_AUDIT_LOG", "logs/tools_audit.jsonl")
Path(os.path.dirname(AUDIT_PATH)).mkdir(parents=True, exist_ok=True)


def _audit_tool(event: str, payload: dict):
    with open(AUDIT_PATH, "a", encoding="utf-8") as f:
        f.write(
            json.dumps(
                {"ts": int(time.time()), "event": event, **payload}, ensure_ascii=False
            )
            + "\n"
        )


def _allowed(tool_name: str) -> bool:
    t = (_PERM.get("tools") or {}).get(tool_name, {})
    return bool(t.get("allowed"))


def execute_tool(tool_name: str, **kwargs):
    if not _allowed(tool_name):
        _audit_tool("DENY", {"tool": tool_name, "kwargs": kwargs})
        raise RuntimeError(f"Tool '{tool_name}' not permitted")
    t0 = time.time()
    try:
        res = TOOL_REGISTRY[tool_name](**kwargs)
        _audit_tool(
            "ALLOW",
            {"tool": tool_name, "lat_ms": (time.time() - t0) * 1000, "kwargs": kwargs},
        )
        return res
    except Exception as e:
        _audit_tool("ERROR", {"tool": tool_name, "err": str(e)})
        raise


# In-memory token bucket per-process; if REDIS_URL set, we’ll back it by Redis for multi-proc.
_RATE: Dict[str, Dict[str, Any]] = {}
_REDIS = None
if os.getenv("REDIS_URL"):
    try:
        from redis import Redis

        _REDIS = Redis.from_url(os.getenv("REDIS_URL"))
    except Exception:
        _REDIS = None


def _rate_ok(key: str, max_req: int, window_s: int = 3600) -> bool:
    now = int(time.time())
    if _REDIS:
        # redis key scheme: rate:{key}:{window}
        win = now // window_s
        rkey = f"rate:{key}:{win}"
        try:
            n = _REDIS.incr(rkey)
            if n == 1:
                _REDIS.expire(rkey, window_s)
            return n <= max_req
        except Exception:
            # fallback to local if redis error
            pass
    # local bucket
    b = _RATE.setdefault(key, {"t0": now, "n": 0})
    if now - b["t0"] >= window_s:
        b["t0"] = now
        b["n"] = 0
    if b["n"] >= max_req:
        return False
    b["n"] += 1
    return True


def _deny(reason: str, ctx: Dict[str, Any]):
    _audit({"allow": False, "reason": reason, **ctx})
    raise PermissionError(reason)


def _match_glob(text: str, glob: str) -> bool:
    # "*.domain.com" style
    pat = re.escape(glob).replace("\\*", ".*")
    return re.fullmatch(pat, text) is not None


# ================== Implementasi Tool (lazy import) ==================


def _tool_code(text: str, **_):
    from javu_agi.tool_code_gen import generate_website_code

    return generate_website_code(text)


def _tool_video(text: str, **_):
    from javu_agi.tool_video_gen import generate_video_script

    return generate_video_script(text)


def _tool_app(text: str, **_):
    from javu_agi.tool_appgen import generate_app_flow

    return generate_app_flow(text)


def _tool_github(_text: str, **_):
    if not _GITHUB_ENABLED:
        _deny("github push disabled by policy", {"tool": "github"})
    from javu_agi.tool_github_push import push_to_github

    return push_to_github("/app")


def _tool_unity(text: str, **_):
    from javu_agi.tool_unity_gen import generate_unity_script

    return generate_unity_script(text)


def _tool_voice(text: str, **_):
    from javu_agi.voice import speak_text

    return speak_text(text)


def _tool_search(_text: str, **_):
    """
    Web-learning/search dengan enforcement:
    - allowed_domains (glob)
    - max_requests_per_task
    - timeout_s
    """
    cfg = _PERM.get("web_search", {})
    if not cfg:
        _deny("web_search disabled by policy", {"tool": "search"})

    allowed = cfg.get("allowed_domains", [])
    max_req = int(cfg.get("max_requests_per_task", 20))
    timeout_s = int(cfg.get("timeout_s", _DEFAULT_TIMEOUT_S))

    # simple per-process rate limit (per tool)
    if not _rate_ok("tool:search", max_req):
        _deny("web_search rate limit exceeded", {"tool": "search"})

    # Enforce downstream via env (kalau pipeline lo respect env)
    os.environ["JAVU_WEB_ALLOWED_DOMAINS"] = ",".join(allowed)
    os.environ["JAVU_WEB_TIMEOUT_S"] = str(timeout_s)
    os.environ["JAVU_WEB_MAX_REQ"] = str(max_req)

    # (opsional) lakukan precheck URL list bila pipeline menerima explicit URLs
    # Kalau pipeline internal yang melakukan crawl, pastikan ia baca env di atas & enforce.

    from javu_agi.web_learning import learn_from_web

    _audit(
        {
            "allow": True,
            "tool": "search",
            "allowed_domains": allowed,
            "max_req": max_req,
            "timeout_s": timeout_s,
        }
    )
    # Panggilan eksternal dibungkus agar kegagalan tidak mematikan executor
    try:
        learn_from_web("system")
        return "Web Learning selesai."
    except Exception as e:
        import logging
        logger = logging.getLogger("javu_agi.tool_executor")
        logger.exception("learn_from_web failed: %s", e)
        return f"[TOOL ERROR] learn_from_web failed: {e}"
    
def _tool_image(text: str, **_):
    from javu_agi.tool_image_gen import generate_image_file

    return generate_image_file(text, user_id="system")


def _tool_eval(text: str, **_):
    from javu_agi.meta_reasoning import verify_output

    return verify_output("system", text, text)


def _tool_shell(cmd: str, **_):
    """
    Shell terkontrol:
    - allowed_cmds (whitelist by first token)
    - deny_patterns (regex)
    - timeout_s
    """
    cfg = _PERM.get("shell", {})
    if not cfg:
        _deny("shell disabled by policy", {"tool": "shell"})

    allowed = set(cfg.get("allowed_cmds", []))
    denies = cfg.get("deny_patterns", [])
    timeout_s = int(cfg.get("timeout_s", _DEFAULT_TIMEOUT_S))

    first = cmd.strip().split(" ")[0]
    if first not in allowed:
        _deny(f"command '{first}' not allowed", {"tool": "shell", "cmd": cmd})

    for pat in denies:
        if re.search(pat, cmd, flags=re.IGNORECASE):
            _deny(f"cmd matches deny pattern: {pat}", {"tool": "shell", "cmd": cmd})

    if not _rate_ok("tool:shell", int(cfg.get("max_requests_per_task", 10))):
        _deny("shell rate limit exceeded", {"tool": "shell"})

    _audit({"allow": True, "tool": "shell", "cmd": cmd})
    try:
        p = subprocess.run(cmd, shell=True, capture_output=True, timeout=timeout_s)
        out = p.stdout.decode("utf-8", "ignore")[:200000]
        err = p.stderr.decode("utf-8", "ignore")[:200000]
        return f"[code={p.returncode}]\n{out}\n{err}"
    except subprocess.TimeoutExpired:
        _deny("shell timeout", {"tool": "shell", "cmd": cmd})


# ================== Registry ==================

# Catatan: tool "shell" menerima string command sebagai input_text.
_REGISTRY: Dict[str, Callable[..., str]] = {
    "code": _tool_code,
    "video": _tool_video,
    "app": _tool_app,
    "github": _tool_github,
    "unity": _tool_unity,
    "voice": _tool_voice,
    "search": _tool_search,
    "image": _tool_image,
    "eval": _tool_eval,
    "shell": _tool_shell,
}

# Apply allowlist (jika diset)
if _ALLOWED:
    _REGISTRY = {k: v for k, v in _REGISTRY.items() if k in _ALLOWED}

# Expose the registry under the legacy name ``TOOL_REGISTRY`` for backward compatibility.
# Some older code still references ``TOOL_REGISTRY`` to dispatch tools by name.
TOOL_REGISTRY: Dict[str, Callable[..., str]] = _REGISTRY

# ================== Planner & Executor ==================


def react_tool_chain(user_input: str) -> List[str]:
    """
    Minta LLM merencanakan urutan tool, enforce allowlist + dedupe + limit panjang.
    """
    prompt = f"""
Kamu adalah AI eksekutor. Dari perintah berikut, tentukan urutan tool yang DIBUTUHKAN.
Perintah:
\"\"\"{user_input}\"\"\"

Balas HANYA dengan nama tool valid (satu per baris) dari set ini:
{sorted(list(_REGISTRY.keys()))}
"""
    plan = call_llm(prompt, task_type="plan", temperature=0.0) or ""
    seq = []
    for line in plan.splitlines():
        t = line.strip()
        if t in _REGISTRY and t not in seq:
            seq.append(t)
        if len(seq) >= 5:  # batasi chain
            break
    return seq


def _run_with_timeout(
    fn: Callable, args: tuple, timeout_s: int = _DEFAULT_TIMEOUT_S
) -> str:
    """
    Eksekusi tool di proses terpisah + timeout. Kalau hang/bermasalah → bunuh.
    """
    q: mp.Queue = mp.Queue()

    def _target():
        try:
            q.put(("ok", fn(*args)))
        except Exception as e:
            q.put(("err", f"{e}\n{traceback.format_exc()}"))

    p = mp.Process(target=_target, daemon=True)
    p.start()
    p.join(timeout_s)
    if p.is_alive():
        p.kill()
        _audit({"allow": False, "reason": "timeout", "tool_proc": fn.__name__})
        return "[TOOL ERROR] timeout"
    status, payload = q.get() if not q.empty() else ("err", "no result")
    return payload if status == "ok" else f"[TOOL ERROR] {payload}"


def execute_tool(tool: str, input_text: str, user_id: str = "system") -> str:
    """
    Eksekusi tool berdasar registry + policy, dengan logging & audit.
    - input_text: untuk tool 'shell' = command; untuk 'code'/'video'/dst = prompt/teks.
    """
    ctx = {"tool": tool, "user": user_id}
    if tool not in _REGISTRY:
        _audit({"allow": False, "reason": "unknown tool", **ctx})
        result = f"[TOOL ERROR] Tool '{tool}' tidak diizinkan/unknown."
    else:
        _audit({"allow": True, "invoke": tool, **ctx})
        result = _run_with_timeout(
            _REGISTRY[tool], (input_text,), timeout_s=_DEFAULT_TIMEOUT_S
        )

    # Log ringkas (hindari bocor data sensitif)
    try:
        log_user(user_id, f"[TOOL] {tool} → {str(result)[:200]}")
    except Exception:
        pass
    return result
