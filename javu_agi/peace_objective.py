from __future__ import annotations
from typing import List, Dict, Any

COOP = [
    "cooperate",
    "collaborate",
    "share",
    "mediate",
    "reconcile",
    "common ground",
    "joint",
]
CONFLICT = [
    "attack",
    "exploit",
    "dominate",
    "surveil",
    "manipulate",
    "suppress",
    "retaliate",
]


class PeaceObjective:
    def evaluate(
        self, plan: List[Dict[str, Any]], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        text = " ".join(map(str, plan)).lower()
        coop = sum(text.count(k) for k in COOP)
        conf = sum(text.count(k) for k in CONFLICT)
        score = max(0.0, min(1.0, 0.5 + 0.12 * coop - 0.15 * conf))
        out = {"cooperation": coop, "conflict": conf, "peace_score": round(score, 3)}
        out["recommendations"] = []
        if conf > 0:
            out["recommendations"].append(
                "Replace adversarial language with cooperative framing."
            )
        if coop == 0:
            out["recommendations"].append(
                "Add a joint review/transparent reporting step."
            )
        return out
