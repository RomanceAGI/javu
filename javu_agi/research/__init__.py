from __future__ import annotations
import importlib, logging

logger = logging.getLogger("javu_agi.research")
__all__ = []


def _imp(mod: str):
    try:
        m = importlib.import_module(f"javu_agi.research.{mod}")
        globals()[mod] = m
        __all__.append(mod)
        return m
    except ModuleNotFoundError:
        logger.debug("research optional missing: %s", mod)
    except Exception as e:
        logger.warning("research import error %s: %s", mod, e)


m = _imp("hypothesis")
try:
    if m and hasattr(m, "HypothesisEngine"):
        from .hypothesis import HypothesisEngine  # type: ignore

        globals()["HypothesisEngine"] = HypothesisEngine
        __all__.append("HypothesisEngine")
except Exception as e:
    logger.debug("HypothesisEngine not available: %s", e)
