"""
JAVU-AGI Arena subsystem (duels, task bank, evaluation).
Max/pro: safe lazy imports + clear public API.
"""

from __future__ import annotations
import importlib, logging

logger = logging.getLogger("javu_agi.arena")

__all__ = []
_modules = ["checker", "task_bank", "scorers", "utils"]


def _imp(name: str):
    try:
        m = importlib.import_module(f"javu_agi.arena.{name}")
        globals()[name] = m
        __all__.append(name)
        return m
    except ModuleNotFoundError:
        logger.debug("arena optional missing: %s", name)
    except Exception as e:
        logger.warning("arena import error %s: %s", name, e)


for _m in _modules:
    _imp(_m)

# Lift common symbols (if exist)
for mod, sym in [("checker", "duel"), ("task_bank", "sample_mix")]:
    try:
        globals()[sym] = getattr(globals()[mod], sym)  # type: ignore
        __all__.append(sym)
    except Exception:
        pass
