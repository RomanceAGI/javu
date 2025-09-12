from __future__ import annotations
import importlib, logging

logger = logging.getLogger("javu_agi.tools")
__all__ = []


def _imp(mod: str):
    try:
        m = importlib.import_module(f"javu_agi.tools.{mod}")
        globals()[mod] = m
        __all__.append(mod)
        return m
    except ModuleNotFoundError:
        logger.debug("tools optional missing: %s", mod)
    except Exception as e:
        logger.warning("tools import error %s: %s", mod, e)


m = _imp("registry")
try:
    if m and hasattr(m, "ToolRegistry"):
        from .registry import ToolRegistry  # type: ignore

        globals()["ToolRegistry"] = ToolRegistry
        __all__.append("ToolRegistry")
except Exception as e:
    logger.debug("ToolRegistry not available: %s", e)
