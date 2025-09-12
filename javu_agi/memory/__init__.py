"""
Memory subsystem (episodic, semantic, policy).
"""

from __future__ import annotations
import importlib, logging

logger = logging.getLogger("javu_agi.memory")
__all__ = []
mods = ["manager", "store", "episodic", "semantic", "policy_memory"]
for _m in mods:
    try:
        m = importlib.import_module(f"javu_agi.memory.{_m}")
        globals()[_m] = m
        __all__.append(_m)
    except ModuleNotFoundError:
        logger.debug("memory optional missing: %s", _m)
    except Exception as e:
        logger.warning("memory import error %s: %s", _m, e)

# common symbols (optional)
for mod, sym in [("manager", "MemoryManager")]:
    try:
        globals()[sym] = getattr(globals()[mod], sym)  # type: ignore
        __all__.append(sym)
    except Exception:
        pass
