import re

_PATTERNS = [
    re.compile(r"\bsk-[A-Za-z0-9]{20,}\b"),  # openai-like
    re.compile(r"\b(ak-|ant-)[A-Za-z0-9]{20,}\b"),  # anthropic-like
    re.compile(r"(?i)\b(api[_-]?key|token)[=:]\s*[A-Za-z0-9_\-]{12,}\b"),
    re.compile(r"(?i)AWS[_-]?SECRET[^A-Za-z0-9]{0,10}[A-Za-z0-9/+]{20,}"),
]


def has_secret(s: str) -> bool:
    if not s or not isinstance(s, str):
        return False
    for rx in _PATTERNS:
        if rx.search(s):
            return True
    return False
