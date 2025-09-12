import os, re

READ_ALLOW = lambda: {
    os.getenv("READ_DIR", "/data"),
    os.getenv("ARTIFACTS_DIR", "/data/artifacts"),
}


def _paths(cmd: str):
    return re.findall(r"(/[^ \t\r\n]+|[A-Za-z]:\\[^ \t\r\n]+)", cmd or "")


def is_read_cmd(tool: str, cmd: str) -> bool:
    t = (tool or "").lower()
    c = (cmd or "").lower()
    return t in {"bash", "python", "cat", "grep"} and any(
        x in c for x in ("cat ", " open(", "grep ")
    )


def allow_read(tool: str, cmd: str, user_ok: bool = False) -> bool:
    if user_ok:
        return True
    if not is_read_cmd(tool, cmd):
        return True
    allow = {d.lower().rstrip("\\/") for d in READ_ALLOW()}
    for p in _paths(cmd):
        pl = p.lower().rstrip("\\/")
        if not any(pl.startswith(a) for a in allow):
            return False
    return True
