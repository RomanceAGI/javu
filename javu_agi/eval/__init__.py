from __future__ import annotations
import importlib, logging

logger = logging.getLogger("javu_agi.eval")
__all__ = []


def _exp(name: str, symbol: str | None = None):
    try:
        m = importlib.import_module(f"javu_agi.eval.{name}")
        if symbol:
            obj = getattr(m, symbol)
            globals()[symbol] = obj
            __all__.append(symbol)
        else:
            globals()[name] = m
            __all__.append(name)
    except ModuleNotFoundError:
        logger.debug("eval optional missing: %s", name)
    except Exception as e:
        logger.warning("eval import error %s: %s", name, e)


# modules / classes commonly used
_exp("eval_harness", None)
_exp("task_runner", None)
try:
    from .eval_harness import EvalHarness  # type: ignore
    from .task_runner import TaskRunner  # type: ignore

    __all__ += ["EvalHarness", "TaskRunner"]
except Exception as e:
    logger.debug("eval symbols not available: %s", e)
