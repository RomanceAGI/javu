from __future__ import annotations
import importlib, logging

logger = logging.getLogger("javu_agi.rag")
__all__ = []
mods = ["index", "retriever", "reader", "ingest"]
for _m in mods:
    try:
        m = importlib.import_module(f"javu_agi.rag.{_m}")
        globals()[_m] = m
        __all__.append(_m)
    except ModuleNotFoundError:
        logger.debug("rag optional missing: %s", _m)
    except Exception as e:
        logger.warning("rag import error %s: %s", _m, e)
