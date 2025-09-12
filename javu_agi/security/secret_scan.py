import re

_PATTERNS = [
    ("openai_key", re.compile(r"\bsk-[A-Za-z0-9]{20,}\b")),
    ("anthropic_key", re.compile(r"\b(ak-|ant-)[A-Za-z0-9]{20,}\b")),
    ("aws_secret", re.compile(r"\b(?=.*AWS).{0,20}SECRET.{0,20}\b", re.IGNORECASE)),
    (
        "generic_api",
        re.compile(r"\b(api[_-]?key|token)[=:]\s*[A-Za-z0-9_\-]{12,}\b", re.IGNORECASE),
    ),
]


def has_secret(s: str) -> bool:
    if not s:
        return False
    for _, rx in _PATTERNS:
        if rx.search(s):
            return True
    return False
