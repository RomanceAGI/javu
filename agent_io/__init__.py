from __future__ import annotations
import importlib, logging
logger = logging.getLogger("agent_io")
__all__ = []
for _m in ["rest", "cli", "events"]:
    try:
        m = importlib.import_module(f"agent_io.{_m}")
        globals()[_m] = m; __all__.append(_m)
    except ModuleNotFoundError:
        logger.debug("agent_io optional missing: %s", _m)
    except Exception as e:
        logger.warning("agent_io import error %s: %s", _m, e)
