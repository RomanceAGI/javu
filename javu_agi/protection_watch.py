import os, time, json, threading
from javu_agi.safety_values import violates_core_values

ALERT_LOG = "/data/audit/alerts.jsonl"


def emit_alert(kind: str, msg: str, meta=None):
    os.makedirs(os.path.dirname(ALERT_LOG), exist_ok=True)
    with open(ALERT_LOG, "a", encoding="utf-8") as f:
        f.write(
            json.dumps(
                {"ts": time.time(), "kind": kind, "msg": msg, "meta": meta or {}}
            )
            + "\n"
        )


def synthesize_mitigation_goal(kind: str, msg: str) -> str:
    # only defensive goals, non-offensive
    return (
        f"Buat rencana mitigasi defensif untuk isu: [{kind}] {msg}. "
        "Cari fakta, rangkum opsi damai, susun tindakan minim risiko & etis."
    )


class FounderProtection:
    def __init__(self, founder_id="roman"):
        self.founder_id = founder_id

    def on_signal(self, kind: str, msg: str):
        emit_alert(kind, msg)
        g = synthesize_mitigation_goal(kind, msg)
        if not violates_core_values(g):
            return {"user": "system", "goal": g, "priority": 0.95}
        return None
