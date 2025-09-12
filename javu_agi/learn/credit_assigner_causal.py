from __future__ import annotations
from typing import List, Dict, Any
import os, json, time

from javu_agi.world_model import WorldModel


class CausalCreditAssigner:
    def __init__(self, out_dir: str = "rewards"):
        self.out_dir = out_dir
        os.makedirs(out_dir, exist_ok=True)

    def assign(
        self, world: WorldModel, steps: List[str], reward: float
    ) -> Dict[str, Any]:
        if not steps:
            return {"assigned": []}
        # counterfactual: measure change in confidence if we "do" emphasize a step feature
        weights = []
        for s in steps:
            try:
                base = world.simulate_action(s).get("expected_confidence", 0.5)
                # probe: increase evidence_quality
                cf = world.do_intervene({"evidence_quality": 0.9}, probe="confidence")
                delta = max(0.0, cf - base)
            except Exception:
                delta = 0.0
            weights.append(delta)
        total = sum(weights) or 1.0
        assigned = [
            {"step": st, "credit": float(reward * (w / total))}
            for st, w in zip(steps, weights)
        ]
        try:
            with open(
                os.path.join(self.out_dir, "credit_causal.jsonl"), "a", encoding="utf-8"
            ) as f:
                f.write(
                    json.dumps(
                        {"ts": int(time.time()), "assigned": assigned},
                        ensure_ascii=False,
                    )
                    + "\n"
                )
        except Exception:
            pass
        return {"assigned": assigned}
