from __future__ import annotations
import importlib, logging

logger = logging.getLogger("javu_agi.world")
__all__ = []
mods = ["sensors", "actuators", "sim"]
for _m in mods:
    try:
        m = importlib.import_module(f"javu_agi.world.{_m}")
        globals()[_m] = m
        __all__.append(_m)
    except ModuleNotFoundError:
        logger.debug("world optional missing: %s", _m)
    except Exception as e:
        logger.warning("world import error %s: %s", _m, e)
