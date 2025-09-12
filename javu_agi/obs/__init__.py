"""
Observation/metrics/tracing subsystem (max/pro init).
Exposes: M (metrics facade), span (tracing) when available.
"""

from __future__ import annotations
import importlib, logging

logger = logging.getLogger("javu_agi.obs")
__all__ = []


def _try(mod: str, symbol: str | None = None):
    try:
        m = importlib.import_module(f"javu_agi.obs.{mod}")
        globals()[mod] = m
        __all__.append(mod)
        if symbol:
            s = getattr(m, symbol)
            globals()[symbol] = s
            __all__.append(symbol)
    except ModuleNotFoundError:
        logger.debug("obs optional missing: %s", mod)
    except Exception as e:
        logger.warning("obs import error %s: %s", mod, e)


_try("metrics")
_try("tracing")

# lift common symbols if exist
for _sym in ("M", "span"):
    try:
        globals()[_sym] = getattr(globals().get("metrics", object()), _sym)  # type: ignore
        __all__.append(_sym)
    except Exception:
        try:
            globals()[_sym] = getattr(globals().get("tracing", object()), _sym)  # type: ignore
            __all__.append(_sym)
        except Exception:
            pass
