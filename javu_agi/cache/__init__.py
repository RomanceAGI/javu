"""
Caching for JAVU-AGI (in-memory/disk).
"""

from __future__ import annotations
import importlib, logging

logger = logging.getLogger("javu_agi.cache")
__all__ = []
for _m in ["memory_cache", "disk_cache"]:
    try:
        m = importlib.import_module(f"javu_agi.cache.{_m}")
        globals()[_m] = m
        __all__.append(_m)
    except ModuleNotFoundError:
        logger.debug("cache optional missing: %s", _m)
    except Exception as e:
        logger.warning("cache import error %s: %s", _m, e)
