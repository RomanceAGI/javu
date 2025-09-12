# === HARD GUARD: disable autotrain in current phase (ToS-safe) ===
try:
    from javu_agi.registry import (
        feature_enabled,
        LLMBuilderDisabledError,
    )  # if you used my registry patch, else fallback
except Exception:

    def feature_enabled(_):
        return False

    class LLMBuilderDisabledError(RuntimeError): ...


if not feature_enabled("LLM_BUILDER_ENABLED"):
    raise LLMBuilderDisabledError("Autotrain disabled: LLM_BUILDER_ENABLED=False")

from .orchestrator import AutoTrainOrchestrator
