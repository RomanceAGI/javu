from __future__ import annotations
from typing import Dict, List
import re

# Tool yang diizinkan (deny-by-default)
ALLOW_TOOLS = {
    "python",  # eksekusi skrip python mini
    "json_filter",  # transform JSON internal
    "jq",  # hanya jika dipanggil via worker
    # tambahkan tool spesifik lain di sini secara eksplisit
}

# Kata/urutan berbahaya (blok keras)
DENY_PATTERNS = [
    r"\b(rm\s+-rf|mkfs|mount|umount|shutdown|reboot|halt)\b",
    r";\s*rm\b",
    r"&\s*rm\b",
    r"\|\s*rm\b",
    r":\(\)\s*{\s*:\|\s*:\s*;\s*}\s*:\s*;",  # fork bomb
    r">\s*/dev/sd[a-z]",
    r">\s*/dev/null\s*2>&1\s*&",  # stealthy redirection
    r"\b(chmod\s+7\d\d|chown\s+root|sudo\s+)",  # privilege ops
    r"/etc/passwd|/etc/shadow",
    r"ssh\s+|scp\s+|sftp\s+|curl\s+|wget\s+|http[s]?://",  # outbound
]

# Karakter/metashell terlarang
DENY_CHARS = set("`$(){}[]|;&><\\")

MAX_CMD_LEN = 8000
MAX_STEPS = 8


class PolicyFilterHard:
    def __init__(self, allow: set[str] | None = None):
        self.allow = allow or ALLOW_TOOLS
        self._deny_re = [re.compile(p, re.I) for p in DENY_PATTERNS]

    def _bad_chars(self, s: str) -> str | None:
        bad = [c for c in s if c in DENY_CHARS]
        return "".join(sorted(set(bad))) if bad else None

    def check(self, plan_steps: List[Dict]) -> Dict:
        if not plan_steps:
            return {"ok": False, "reason": "empty plan"}
        if len(plan_steps) > MAX_STEPS:
            return {
                "ok": False,
                "reason": f"too many steps ({len(plan_steps)}>{MAX_STEPS})",
            }

        for i, step in enumerate(plan_steps):
            tool = (step.get("tool") or "").strip()
            cmd = (step.get("cmd") or "").strip()

            if tool not in self.allow:
                return {"ok": False, "reason": f"tool not allowed: {tool}"}

            if not cmd or len(cmd) > MAX_CMD_LEN:
                return {"ok": False, "reason": f"invalid cmd length at step {i}"}

            bc = self._bad_chars(cmd)
            if bc:
                return {
                    "ok": False,
                    "reason": f"forbidden shell meta-chars at step {i}: {bc}",
                }

            for rx in self._deny_re:
                if rx.search(cmd):
                    return {"ok": False, "reason": f"denied pattern at step {i}"}

        return {"ok": True, "reason": "ok"}
