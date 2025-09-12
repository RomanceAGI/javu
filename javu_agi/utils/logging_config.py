"""# centralized logging configuration and helpers
import logging
import re
from typing import Any, Dict

SENSITIVE_KEYS = {"password", "passwd", "secret", "api_key", "token", "auth", "access_token"}

REDACT_RE = re.compile("|".join(re.escape(k) for k in SENSITIVE_KEYS), re.IGNORECASE)

def redact(obj: Any) -> Any:
    """Redact obvious sensitive strings inside dicts/strings for safe logging/artifacts."""
    try:
        if isinstance(obj, dict):
            out = {}
            for k, v in obj.items():
                if any(s in k.lower() for s in SENSITIVE_KEYS):
                    out[k] = "<REDACTED>"
                else:
                    out[k] = redact(v)
            return out
        if isinstance(obj, list):
            return [redact(x) for x in obj]
        if isinstance(obj, str):
            # redact any token-like patterns
            s = obj
            s = REDACT_RE.sub("<REDACTED>", s)
            # trim very long strings
            if len(s) > 2000:
                return s[:2000] + "...[truncated]"
            return s
    except Exception:
        return "<UNSERIALIZABLE>"
    return obj

def configure_logging(level: int = logging.INFO) -> None:
    """Configure root logger with a sane formatter. Call at app startup."""
    root = logging.getLogger()
    if root.handlers:
        return
    handler = logging.StreamHandler()
    fmt = "%\(asctime\)s %\(levelname\)s %\(name\)s: %\(message\)s"
    handler.setFormatter(logging.Formatter(fmt))
    root.addHandler(handler)
    root.setLevel(level)

def get_logger(name: str):
    configure_logging()
    return logging.getLogger(name)
"""