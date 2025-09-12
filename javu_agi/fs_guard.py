import os, re

ALLOW_DIRS = lambda: {
    os.getenv("WRITE_DIR", "/data"),
    os.getenv("ARTIFACTS_DIR", "/data/artifacts"),
}
DANGEROUS = [
    r"\b/etc\b",
    r"\b/var\b",
    r"\b/windows\b",
    r"\bc:\\windows\\",
    r"\b/home/[^/]+/(?!allowed)",
]


def is_write_like(cmd: str) -> bool:
    low = cmd.lower()
    return any(t in low for t in (">", ">>", " tee ", " mv ", " cp ", " rm "))


def extract_paths(cmd: str):
    return re.findall(r"(/[^ \t\r\n]+|[A-Za-z]:\\[^ \t\r\n]+)", cmd)


def allowed_write(cmd: str) -> bool:
    if not is_write_like(cmd):
        return True
    paths = extract_paths(cmd)
    if not paths:
        return True
    allow = {p.lower().rstrip("\\/") for p in ALLOW_DIRS()}
    for p in paths:
        pl = p.lower().rstrip("\\/")
        if any(d in pl for d in ("/etc", "/var", "c:\\windows")):  # quick kill
            return False
        if not any(pl.startswith(a) for a in allow):
            return False
    return True
