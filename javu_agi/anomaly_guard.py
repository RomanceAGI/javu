import re
from types import SimpleNamespace

_susp = [
    r"base64\s+-d",
    r"curl\s+.*\|.*sh",
    r"wget\s+.*\|.*sh",
    r"pip\s+install\s+.+ -U",
    r"ssh\s+.*\@",
    r"python\s+-c\s+['\"]import\s+os;os\.system",
    r"rm\s+-rf\s+/",
]
RX = [re.compile(p, re.I) for p in _susp]


class AnomalyGuard:
    def check_cmd(self, cmd: str):
        t = cmd or ""
        for rx in RX:
            if rx.search(t):
                return SimpleNamespace(allow=False, reason="anomaly:suspicious_cmd")
        if len(t) > 8000:
            return SimpleNamespace(allow=False, reason="anomaly:payload_too_long")
        return SimpleNamespace(allow=True, reason="")
