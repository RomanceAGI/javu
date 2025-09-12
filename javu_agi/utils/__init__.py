from __future__ import annotations
import importlib, logging

logger = logging.getLogger("javu_agi.utils")
__all__ = []
mods = ["logger", "io", "timing", "text", "ids"]
for _m in mods:
    try:
        m = importlib.import_module(f"javu_agi.utils.{_m}")
        globals()[_m] = m
        __all__.append(_m)
    except ModuleNotFoundError:
        logger.debug("utils optional missing: %s", _m)
    except Exception as e:
        logger.warning("utils import error %s: %s", _m, e)

# lift common logger helpers if present
for sym in ("log_user", "log_system"):
    try:
        globals()[sym] = getattr(globals()["logger"], sym)  # type: ignore
        __all__.append(sym)
    except Exception:
        pass
