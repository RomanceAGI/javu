# === HARD GUARD: disable train package auto-import side effects ===
from __future__ import annotations

try:
    from javu_agi.registry import feature_enabled, LLMBuilderDisabledError
except Exception:

    def feature_enabled(_):
        return False

    class LLMBuilderDisabledError(RuntimeError): ...


import logging, importlib

logger = logging.getLogger("javu_agi.train")

__all__ = []

if not feature_enabled("LLM_BUILDER_ENABLED"):
    logger.warning("train package guarded: LLM builder OFF")
