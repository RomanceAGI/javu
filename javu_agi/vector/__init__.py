from __future__ import annotations
import importlib, logging

logger = logging.getLogger("javu_agi.vector")
__all__ = []
mods = ["backends", "faiss_backend", "pgvector_backend"]
for _m in mods:
    try:
        m = importlib.import_module(f"javu_agi.vector.{_m}")
        globals()[_m] = m
        __all__.append(_m)
    except ModuleNotFoundError:
        logger.debug("vector optional missing: %s", _m)
    except Exception as e:
        logger.warning("vector import error %s: %s", _m, e)
