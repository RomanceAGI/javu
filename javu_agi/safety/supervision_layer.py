from typing import List, Tuple, Dict, Any


class SupervisionLayer:
    def __init__(self, ethics_checker, safety_checker, policy_checker):
        self.ethics = ethics_checker
        self.safety = safety_checker
        self.policy = policy_checker

    def supervise(
        self, actions: List[str], context: dict
    ) -> Tuple[bool, Dict[str, Any]]:
        reasons = {}
        ethical = getattr(self.ethics, "check", lambda a: True)(actions)
        if not ethical:
            reasons["ethics"] = "violation"
        safe = getattr(self.safety, "check", lambda a: True)(actions)
        if not safe:
            reasons["safety"] = "violation"
        policy_ok = getattr(self.policy, "check", lambda c: True)(context)
        if not policy_ok:
            reasons["policy"] = "violation"

        ok = len(reasons) == 0
        # Beri hint untuk EC: DENY jika ethics/safety gagal; ESCALATE kalau policy gagal
        hint = "approve"
        if "ethics" in reasons or "safety" in reasons:
            hint = "deny"
        elif "policy" in reasons:
            hint = "escalate"
        return ok, {
            "reasons": reasons,
            "hint": hint,
            "actions": actions,
            "context": context,
        }
