import re

_ANSI_RE = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
_SECRET_RE = re.compile(
    r"(?i)(sk-[A-Za-z0-9]{20,}|api[_-]?key\s*[:=]\s*[A-Za-z0-9_\-]{12,})"
)


def strip_ansi(s: str) -> str:
    if not isinstance(s, str):
        return s
    return _ANSI_RE.sub("", s)


def scrub(s: str) -> str:
    if not isinstance(s, str):
        return s
    x = strip_ansi(s)
    # redaksi kasar secret
    x = _SECRET_RE.sub("[REDACTED]", x)
    # normalisasi whitespace panjang
    return "\n".join(line.rstrip() for line in x.splitlines())
