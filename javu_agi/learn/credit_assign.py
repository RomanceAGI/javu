from __future__ import annotations
from typing import List, Dict


class CreditAssigner:
    """
    Hitung credit per-step dari simulasi plan:
    - input: sim["nodes"] = [{"expected_confidence": float, "step_cost": float, "risk_level": str}, ...]
    - output: list credit ([-1..1]) dengan sum ~ final_reward (distribusi advantage)
    """

    def __init__(self, risk_penalty: dict | None = None):
        self.risk_pen = risk_penalty or {"low": 0.0, "medium": 0.2, "high": 0.5}

    def assign(self, nodes: List[Dict], final_reward: float) -> List[float]:
        if not nodes:
            return []
        confs = [float(n.get("expected_confidence", 0.5)) for n in nodes]
        costs = [max(1e-6, float(n.get("step_cost", 1.0))) for n in nodes]
        risks = [self.risk_pen.get(str(n.get("risk_level", "low")), 0.0) for n in nodes]

        # advantage vs mean confidence, penalize risk, lightly penalize high cost
        c_mean = sum(confs) / len(confs)
        adv = []
        for c, cost, r in zip(confs, costs, risks):
            a = (c - c_mean) - r - 0.02 * cost
            adv.append(a)

        # normalize to [-1,1] and scale to final reward magnitude
        max_abs = max(1e-6, max(abs(x) for x in adv))
        adv = [x / max_abs for x in adv]

        # distribute final reward sign/magnitude (cap to [-1,1])
        # final_reward expected ~ [-1..+1] per shaping
        scale = max(-1.0, min(1.0, final_reward))
        credits = [max(-1.0, min(1.0, x * scale)) for x in adv]
        return credits
