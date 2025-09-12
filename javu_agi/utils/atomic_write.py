"""
Atomic file helpers: append_jsonl_atomic and write_atomic.
append_jsonl_atomic uses os.open with O_APPEND to reduce race corruption on POSIX.
write_atomic writes to temp file then os.replace.
"""
from __future__ import annotations
import os
import tempfile
from typing import Any
from javu_agi.utils.logging_config import get_logger

logger = get_logger("javu_agi.atomic_write")


def append_jsonl_atomic(path: str, line: str) -> None:
    b = (line.rstrip("\n") + "\n").encode("utf-8")
    try:
        flags = os.O_WRONLY | os.O_CREAT | os.O_APPEND
        # mode 0o644
        fd = os.open(path, flags, 0o644)
        try:
            os.write(fd, b)
        finally:
            os.close(fd)
    except Exception:
        logger.exception("Failed atomic append to %s", path)
        # fallback: try simple open append
        try:
            with open(path, "a", encoding="utf-8") as f:
                f.write(line + "\n")
        except Exception:
            logger.exception("Fallback append also failed for %s", path)


def write_atomic(path: str, content: str) -> None:
    d = os.path.dirname(path) or "."
    os.makedirs(d, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=d, prefix=".tmp_write_")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(content)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    except Exception:
        logger.exception("Atomic write failed for %s", path)
        try:
            if os.path.exists(tmp):
                os.remove(tmp)
        except Exception:
            pass