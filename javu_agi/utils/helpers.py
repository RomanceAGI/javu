from __future__ import annotations
import os, sys, time, json, uuid, importlib, traceback
from typing import Any, Dict


# --------- TRACE / ID ----------
def gen_trace(prefix: str = "trace") -> str:
    """Generate unique trace id."""
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def short_id() -> str:
    return uuid.uuid4().hex[:8]


# --------- LOGGING ----------
def log(msg: str, level: str = "INFO", trace: str | None = None):
    """Simple stdout logger with timestamp."""
    t = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    tr = f" trace={trace}" if trace else ""
    sys.stdout.write(f"[{t}] [{level}] {msg}{tr}\n")
    sys.stdout.flush()


def log_error(err: Exception, where: str = "", trace: str | None = None):
    log(f"ERROR in {where}: {err}", level="ERROR", trace=trace)
    tb = traceback.format_exc()
    sys.stdout.write(tb + "\n")
    sys.stdout.flush()


# --------- JSON I/O ----------
def json_dump(data: Any, path: str):
    """Dump dict/list ke file JSON pretty."""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def json_load(path: str) -> Any:
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def json_appendl(data: Dict[str, Any], path: str):
    """Append dict ke file .jsonl"""
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(data, ensure_ascii=False) + "\n")


# --------- SAFE IMPORT ----------
def safe_import(module: str):
    """Try import modul opsional. Return module atau None."""
    try:
        return importlib.import_module(module)
    except ImportError:
        return None
    except Exception:
        traceback.print_exc()
        return None


# --------- ENV ----------
def getenv(key: str, default: str = "") -> str:
    return os.getenv(key, default)


def require_env(key: str) -> str:
    v = os.getenv(key)
    if not v:
        raise RuntimeError(f"Missing required env: {key}")
    return v
