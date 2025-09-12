from __future__ import annotations
import os, time
from typing import Any, Dict

def snapshot(controller) -> Dict[str, Any]:
    try:
        router = getattr(controller, "router", None)
        router_status = router.status() if hasattr(router, "status") else {}
    except Exception:
        router_status = {}

    try:
        quota = controller.quota.per_user if hasattr(controller, "quota") else {}
        # summarize
        plans = {}
        for uid, s in quota.items():
            plans[s["plan"]] = plans.get(s["plan"], 0) + 1
        quota_state = {"users": len(quota), "plans": plans}
    except Exception:
        quota_state = {}

    try:
        rate = getattr(controller.limit_mgr, "user_rpm", {})
        avg_rpm = sum(rate.values())/max(1,len(rate))
    except Exception:
        avg_rpm = 0

    return {
        "ts": int(time.time()),
        "caps": {
            "api": {
                "avg_rpm": avg_rpm,
                "limits_defined": bool(rate),
            },
            "router": router_status.get("caps") if isinstance(router_status, dict) else {},
        },
        "router_backends": router_status.get("providers",{}) if isinstance(router_status, dict) else {},
        "flags": {
            "DEV_FAST": os.getenv("DEV_FAST","0"),
            "KILL_SWITCH": os.getenv("KILL_SWITCH","0"),
        }
    }
