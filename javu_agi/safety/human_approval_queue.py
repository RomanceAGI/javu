"""
Simple human-approval queue backed by JSONL (append-only).
Workers should poll get_pending() and call approve/reject.
Approval writes to approvals/decisions.jsonl for traceability.

This is intentionally minimal and synchronous to be easy to review.
"""
from __future__ import annotations
import json
import time
import uuid
import os
from typing import Dict, Any, List, Optional
from javu_agi.utils.logging_config import get_logger, redact
from javu_agi.utils.atomic_write import append_jsonl_atomic

logger = get_logger("javu_agi.safety.human_approval")

QUEUE_PATH = os.path.join(os.getenv("ARTIFACTS_DIR", "artifacts"), "approvals", "queue.jsonl")
DECISIONS_PATH = os.path.join(os.getenv("ARTIFACTS_DIR", "artifacts"), "approvals", "decisions.jsonl")
os.makedirs(os.path.dirname(QUEUE_PATH), exist_ok=True)


def request_approval(actor: str, action: Dict[str, Any], reason: str = "") -> str:
    rid = f"{int(time.time())}_{uuid.uuid4().hex[:8]}"
    item = {"rid": rid, "ts": int(time.time()), "actor": actor, "action": redact(action), "reason": reason, "status": "pending"}
    append_jsonl_atomic(QUEUE_PATH, json.dumps(item, ensure_ascii=False))
    logger.info("Approval requested rid=%s actor=%s reason=%s", rid, actor, reason)
    return rid


def _read_jsonl(path: str) -> List[Dict[str, Any]]:
    items = []
    if not os.path.exists(path):
        return items
    try:
        with open(path, "r", encoding="utf-8") as f:
            for l in f:
                if not l.strip():
                    continue
                try:
                    items.append(json.loads(l))
                except Exception:
                    continue
    except Exception:
        logger.exception("Failed to read jsonl %s", path)
    return items


def get_pending() -> List[Dict[str, Any]]:
    return [i for i in _read_jsonl(QUEUE_PATH) if i.get("status") == "pending"]


def decide(rid: str, approver: str, allow: bool, note: Optional[str] = None) -> bool:
    decision = {"rid": rid, "ts": int(time.time()), "approver": approver, "allow": bool(allow), "note": note or ""}
    append_jsonl_atomic(DECISIONS_PATH, json.dumps(decision, ensure_ascii=False))
    logger.info("Approval decision rid=%s approver=%s allow=%s", rid, approver, allow)
    return True