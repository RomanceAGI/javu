from __future__ import annotations
import importlib
import logging

__version__ = "0.1.0"

# keep logging minimal; main app configures handlers/levels
logger = logging.getLogger("javu_agi")

# modules we want importable as javu_agi.<name>
_PUBLIC = [
    "core",
    "core_loop",
    "main",
    "main_agi_loop",
    "run_arena",
    "tool_executor",
    "tool_code_gen",
    "agi_manager",
    "executive_controller",
    "api",
]


def _safe_import(name: str):
    try:
        return importlib.import_module(f"javu_agi.{name}")
    except ModuleNotFoundError:
        logger.debug("optional module missing: %s", name)
    except Exception as e:
        logger.warning("error importing %s: %s", name, e)


for _m in _PUBLIC:
    mod = _safe_import(_m)
    if mod is not None:
        globals()[_m] = mod

__all__ = _PUBLIC + ["__version__"]
