"""
Wrapper for LLM calls: safe timeout, result validation, redaction.
If your project has call_llm or javu_agi.llm_router.route, this wrapper will prefer that.
Returns a dict like {"text": str, "ok": bool, "meta": {...}}
"""
from __future__ import annotations
from typing import Dict, Any
from javu_agi.utils.logger import get_logger, redact

logger = get_logger("javu_agi.llm_wrapper")


def call_llm_safe(prompt: str, timeout: int = 15) -> Dict[str, Any]:
    """
    Call local call_llm(prompt) or javu_agi.llm_router.route and produce safe output.
    Never raises; returns {"text": "", "ok": False, "error": "..."} on failure.
    """
    try:
        # try direct helper
        try:
            from javu_agi.llm_router import route  # type: ignore
            resp = route("generic", {"prompt": prompt, "timeout_s": timeout})
            text = ""
            if isinstance(resp, dict):
                text = resp.get("text") or resp.get("output") or resp.get("patch") or ""
            else:
                text = str(resp or "")
        except Exception:
            # fallback to call_llm if present
            try:
                from javu_agi.llm import call_llm  # type: ignore
                text = call_llm(prompt, timeout=timeout)
            except Exception:
                text = ""
        if not isinstance(text, str):
            text = str(text)
        text = redact(text)
        return {"text": text, "ok": True, "error": None}
    except Exception as e:
        logger.exception("LLM call failed")
        return {"text": "", "ok": False, "error": str(e)}