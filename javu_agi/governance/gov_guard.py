import os, re
from types import SimpleNamespace

DEFAULT_DENY = [
    r"(^|\b)rm\s+-rf\b",
    r":\(\){:|:&};:",
    r"\bshutdown\b",
    r"\breboot\b",
    r"\bDROP\s+TABLE\b",
    r"\bmkfs\.",
    r"wget\s+http",
    r"curl\s+http.*\|.*sh",
]


class GovGuard:
    def __init__(self, policy_path: str | None = None):
        self.policy_path = policy_path or os.getenv("SAFETY_POLICY", "")
        self._deny = [re.compile(p, re.I) for p in DEFAULT_DENY]
        self._net_allowed = os.getenv("ALLOW_NET", "0").lower() in {"1", "true", "yes"}

    def _check(self, text: str):
        t = text or ""
        for rx in self._deny:
            if rx.search(t):
                return SimpleNamespace(
                    allow=False, category="gov:deny", reason="pattern_match"
                )
        if not self._net_allowed and re.search(r"\b(curl|wget)\b", t, re.I):
            return SimpleNamespace(
                allow=False, category="gov:net", reason="network_disabled"
            )
        return SimpleNamespace(allow=True, category="", reason="")

    def guard_input(self, text: str):
        return self._check(text)

    def guard_output(self, text: str):
        return self._check(text)
