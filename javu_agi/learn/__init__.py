from __future__ import annotations
import importlib, logging

logger = logging.getLogger("javu_agi.learn")
__all__ = []


def _imp(mod: str):
    try:
        return importlib.import_module(f"javu_agi.learn.{mod}")
    except ModuleNotFoundError:
        logger.debug("learn optional missing: %s", mod)
    except Exception as e:
        logger.warning("learn import error %s: %s", mod, e)


for _m in ["policy_learner", "credit", "metrics", "curriculum", "curriculum_gen"]:
    m = _imp(_m)
    if m is not None:
        globals()[_m] = m
        __all__.append(_m)

# common symbols (optional)
try:
    from .policy_learner import PolicyLearner  # type: ignore

    __all__.append("PolicyLearner")
except Exception:
    pass
try:
    from .credit import CreditAssigner  # type: ignore

    __all__.append("CreditAssigner")
except Exception:
    pass
try:
    from .metrics import Metrics  # type: ignore

    __all__.append("Metrics")
except Exception:
    pass
