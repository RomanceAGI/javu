# helper integration for ExecutiveController (preflight, approval polling, audit/cb hooks)
from __future__ import annotations
import time
from typing import Dict, Any, Optional
from javu_agi.utils.logging_config import get_logger, redact
from javu_agi.safety.policy_checker import evaluate_request
from javu_agi.safety.action_audit import record_action
from javu_agi.safety.human_approval_queue import request_approval, _read_jsonl, DECISIONS_PATH
from javu_agi.safety.circuit_breaker import CB

logger = get_logger("javu_agi.safety.ec_integration")

def preflight_action(user_id: str, action: Dict[str, Any]) -> Dict[str, Any]:
    payload = {"actor": user_id, "cmd": action.get("cmd",""), "prompt": action.get("prompt",""), "context": action.get("context", {})}
    decision = evaluate_request(payload)
    try:
        record_action(user_id, action, {"policy": decision})
    except Exception:
        logger.exception("audit failed in preflight_action")
    if not decision.get("allow", False):
        if decision.get("max_severity") == "high":
            CB.record_failure()
            return {"allow": False, "mode": "block", "decision": decision}
        if decision.get("max_severity") == "medium":
            rid = request_approval(user_id, action, reason="auto:policy_medium")
            return {"allow": False, "mode": "pending", "approval_rid": rid, "decision": decision}
        CB.record_failure()
        return {"allow": False, "mode": "block", "decision": decision}
    return {"allow": True, "mode": "allow", "decision": decision}

def is_approved(rid: str) -> Optional[Dict[str,Any]]:
    try:
        items = _read_jsonl(DECISIONS_PATH)
        for d in items:
            if d.get("rid")==rid:
                return d
    except Exception:
        logger.exception("is_approved read failed")
    return None

def enforce_approval_blocking(rid: str, timeout_s: int = 10) -> Dict[str,Any]:
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        d = is_approved(rid)
        if d is not None:
            return {"approved": bool(d.get("allow")), "decision": d}
        time.sleep(0.5)
    return {"approved": False, "decision": None}