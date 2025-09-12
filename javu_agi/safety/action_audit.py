"""
Action auditing and provenance recording.

Records structured events to artifacts/audit.jsonl using atomic append.
All stored content is redacted via logging_config.redact before writing.
"""
from __future__ import annotations
import json
import time
from typing import Dict, Any
from javu_agi.utils.logging_config import get_logger, redact
from javu_agi.utils.atomic_write import append_jsonl_atomic
import os

logger = get_logger("javu_agi.safety.action_audit")
AUDIT_PATH = os.path.join(os.getenv("ARTIFACTS_DIR", "artifacts"), "audit.jsonl")
os.makedirs(os.path.dirname(AUDIT_PATH), exist_ok=True)


def record_action(actor: str, action: Dict[str, Any], decision: Dict[str, Any]) -> None:
    """
    Persist a single audit record:
    action: planned action (cmd/prompt/goal/context)
    decision: policy verdict, approval status, provenance info
    """
    try:
        rec = {
            "ts": int(time.time()),
            "actor": actor,
            "action": redact(action),
            "decision": redact(decision),
        }
        append_jsonl_atomic(AUDIT_PATH, json.dumps(rec, ensure_ascii=False))
        logger.info("Audit recorded for actor=%s decision=%s", actor, redact(decision))
    except Exception:
        logger.exception("Failed to record audit")