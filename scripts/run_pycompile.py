from __future__ import annotations
import os, sys, py_compile

ROOT = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
EXIT = 0

def should_skip(path: str) -> bool:
    parts = path.split(os.sep)
    skip_dirs = {"venv", ".venv", ".git", "build", "dist", "__pycache__"}
    return any(s in parts for s in skip_dirs)

for base, dirs, files in os.walk(ROOT):
    if should_skip(base):
        dirs[:] = []  # don't descend
        continue
    for f in files:
        if f.endswith(".py"):
            p = os.path.join(base, f)
            try:
                py_compile.compile(p, doraise=True)
            except Exception as e:  # noqa: BLE001
                print(f"COMPILE ERROR: {p}: {e}", file=sys.stderr)
                EXIT = 1

sys.exit(EXIT)
