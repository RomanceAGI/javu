from __future__ import annotations
import importlib
import logging

logger = logging.getLogger("javu_agi.runtime")
__all__ = []

# Semua modul runtime yang ada
_modules = [
    "agent_trace",
    "api_router",
    "audit_evaluator",
    "eval_loader",
    "log_server",
    "loop_regression",
    "run_agent",
    "run_multi_agent",
    "run_multi_user",
    "run_rest",
    "sandbox_runner",
    "state_persistance",
    "user_manager",
]


def _imp(name: str):
    """Lazy import + error handling."""
    try:
        m = importlib.import_module(f"javu_agi.runtime.{name}")
        globals()[name] = m
        __all__.append(name)
        logger.debug("Loaded runtime module: %s", name)
        return m
    except ModuleNotFoundError:
        logger.debug("Optional runtime module missing: %s", name)
    except Exception as e:
        logger.warning("Error loading runtime module %s: %s", name, e)


# Import semua modul
for _m in _modules:
    _imp(_m)

# Public API dari beberapa modul kunci
public_symbols = {
    "api_router": ["ApiRouter"],
    "sandbox_runner": ["SandboxRunner"],
    "user_manager": ["UserManager"],
}

for mod, symbols in public_symbols.items():
    if mod in globals():
        for sym in symbols:
            try:
                globals()[sym] = getattr(globals()[mod], sym)  # type: ignore
                __all__.append(sym)
            except AttributeError:
                pass
