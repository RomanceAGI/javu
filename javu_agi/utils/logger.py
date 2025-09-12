from __future__ import annotations
import os, sys, json, time
from typing import Any, Dict

LOG_DIR = os.getenv("LOG_DIR", "logs")
WRITE_FILES = os.getenv("LOG_WRITE_FILES", "0") == "1"


def _ts() -> int:
    return int(time.time())


def _emit(record: Dict[str, Any], fname: str | None = None):
    # stdout (utama untuk Docker)
    sys.stdout.write(json.dumps(record, ensure_ascii=False) + "\n")
    sys.stdout.flush()
    # optional file
    if WRITE_FILES and fname:
        os.makedirs(LOG_DIR, exist_ok=True)
        path = os.path.join(LOG_DIR, fname)
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")


def log_user(user_id: str, message: str, level: str = "INFO"):
    record = {"ts": _ts(), "level": level, "user_id": user_id, "msg": message}
    _emit(record, f"{user_id}.log")


def log_system(message: str, level: str = "INFO", **kw):
    record = {"ts": _ts(), "level": level, "msg": message}
    if kw:
        record.update(kw)
    _emit(record, "system.log")


# -----------------------------------------------------------------------------
# Shorthand logging levels
#
# Some modules import ``debug``/``info`` style helpers from this logger. Define
# simple wrappers to route these calls through ``log_system`` with the
# appropriate severity.  These helpers accept arbitrary keyword arguments
# that are forwarded to the underlying log record.

def debug(message: str, **kw) -> None:
    """Log a debug‑level message to the system logger."""
    log_system(message, level="DEBUG", **kw)


def info(message: str, **kw) -> None:
    """Log an info‑level message to the system logger."""
    log_system(message, level="INFO", **kw)


def warning(message: str, **kw) -> None:
    """Log a warning‑level message to the system logger."""
    log_system(message, level="WARNING", **kw)


def error(message: str, **kw) -> None:
    """Log an error‑level message to the system logger."""
    log_system(message, level="ERROR", **kw)
