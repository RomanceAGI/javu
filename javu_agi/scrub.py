import re

ANSI = re.compile(r"\x1B\[[0-?]*[ -/]*[@-~]")


def strip_ansi(s: str) -> str:
    return ANSI.sub("", s or "")[:20000]  # cap panjang
