from javu_agi.policy_enforcer import PolicyStore
from javu_agi.decision_record import write as write_decision

POLICY = PolicyStore()


def decide(plan, risk, context, intent_id):
    # 1) hard constraints
    for hc in POLICY.ethics["hard_constraints"]:
        if match(hc["match"], plan, risk):
            return "deny", hc["id"]
    # 2) risk threshold → escalate
    if risk.get("score", 0) >= 0.7:
        return "escalate", "HC-002"
    # 3) default
    return "approve", None


def enforce(plan, risk, context, intent_id, world):
    verdict, policy_id = decide(plan, risk, context, intent_id)
    write_decision(
        {
            "intent_id": intent_id,
            "plan": plan,
            "risk": risk,
            "verdict": verdict,
            "world_model": world,
            "tools": [s["tool"] for s in plan],
            "context": context,
        }
    )
    if verdict == "approve":
        return True
    if verdict == "escalate":
        raise PermissionError("Escalate: human approval required")
    raise PermissionError(f"Denied by policy {policy_id}")
