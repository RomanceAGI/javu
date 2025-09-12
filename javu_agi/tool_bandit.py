import math, random, time
from typing import Dict, Optional


class ToolBandit:
    def __init__(self):
        # per tool: successes, failures, ewma_latency, ewma_cost
        self.stats: Dict[str, Dict[str, float]] = {}

    def record(self, tool: str, success: bool, latency_s: float, cost_usd: float):
        s = self.stats.setdefault(tool, {"s": 1.0, "f": 1.0, "lat": 1.0, "cost": 0.01})
        if success:
            s["s"] += 1.0
        else:
            s["f"] += 1.0
        s["lat"] = 0.8 * s["lat"] + 0.2 * max(0.05, latency_s)
        s["cost"] = 0.8 * s["cost"] + 0.2 * max(0.0001, cost_usd)

    def pick(self, candidates):
        # Thompson sampling (Beta) + penalize latency & cost
        best, score = None, -1e9
        for t in candidates:
            s = self.stats.setdefault(t, {"s": 1.0, "f": 1.0, "lat": 1.0, "cost": 0.01})
            p = random.betavariate(s["s"], s["f"])
            val = p - 0.1 * math.log1p(s["lat"]) - 0.2 * math.log1p(100 * s["cost"])
            if val > score:
                best, score = t, val
        return best or candidates[0]
