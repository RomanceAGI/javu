from __future__ import annotations
import time, json, hashlib
from typing import Any, Dict, List


def explain(
    request: Dict[str, Any], response: Dict[str, Any], guards: Dict[str, Any], dt: float
) -> Dict[str, Any]:
    h = hashlib.sha1(
        json.dumps(
            {"u": request.get("user_id"), "p": request.get("prompt")},
            ensure_ascii=False,
        ).encode()
    ).hexdigest()[:12]
    return {
        "id": h,
        "ts": int(time.time()),
        "duration_s": round(dt, 4),
        "model": response.get("model"),
        "status": response.get("status"),
        "error": response.get("error"),
        "guards": guards,
        "summary": {
            "intent": request.get("intent") or "general",
            "tools": request.get("tools") or [],
            "notes": "decision generated under vendor-only; no training or distillation performed",
        },
    }
