"""
Tracing utilities (spans, exporters).
"""
from __future__ import annotations
import importlib, logging
logger = logging.getLogger("trace")
__all__ = []
try:
    tracing = importlib.import_module("trace.tracing")
    globals()["tracing"] = tracing; __all__.append("tracing")
except Exception as e:
    logger.debug("trace optional: %s", e)
