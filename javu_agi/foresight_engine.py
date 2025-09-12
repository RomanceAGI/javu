from __future__ import annotations
import random, math
from typing import Dict, Any, List


class ForesightEngine:
    def __init__(
        self,
        seed: int | None = None,
        horizons: List[int] | None = None,
        samples: int = 200,
    ):
        self.rng = random.Random(seed)
        self.horizons = horizons or [10, 20, 30]
        self.samples = max(50, int(samples))

    def simulate(self, plan_text: str) -> Dict[str, Any]:
        # simple Monte Carlo on three axes
        def draw(base):
            return max(0.0, min(1.0, base + self.rng.uniform(-0.2, 0.2)))

        base_opt = 0.55 + 0.2 * ("peace" in plan_text)
        base_stab = 0.55 - 0.2 * ("conflict" in plan_text)
        base_risk = 0.35 + 0.2 * ("surveil" in plan_text or "exploit" in plan_text)
        by_h = {}
        for h in self.horizons:
            opt = sum(draw(base_opt) for _ in range(self.samples)) / self.samples
            stab = sum(draw(base_stab) for _ in range(self.samples)) / self.samples
            risk = sum(draw(base_risk) for _ in range(self.samples)) / self.samples
            by_h[h] = {
                "optimism": round(opt, 3),
                "stability": round(stab, 3),
                "risk": round(risk, 3),
            }
        return {"horizons": by_h}
