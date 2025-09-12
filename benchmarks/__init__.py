from __future__ import annotations
import importlib, logging
logger = logging.getLogger("benchmarks")
__all__ = []
for _m in ["mmlu", "gsm8k", "custom"]:
    try:
        m = importlib.import_module(f"benchmarks.{_m}")
        globals()[_m] = m; __all__.append(_m)
    except ModuleNotFoundError:
        logger.debug("benchmarks optional missing: %s", _m)
    except Exception as e:
        logger.warning("benchmarks import error %s: %s", _m, e)
