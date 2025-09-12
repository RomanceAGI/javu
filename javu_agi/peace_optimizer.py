from __future__ import annotations
from typing import List, Dict


class PeaceOptimizer:
    def score(self, steps: List[dict]) -> float:
        # skor sederhana: penalti kata/aksi yang memicu konflik & resource contention
        penalty = 0.0
        for s in steps or []:
            t = (s.get("cmd", "") + " " + s.get("tool", "")).lower()
            if any(k in t for k in ["attack", "leak", "exploit", "harass", "troll"]):
                penalty += 0.3
            if any(k in t for k in ["mining", "gpu 100%", "fork bomb"]):
                penalty += 0.2
        return max(0.0, 1.0 - penalty)

    def optimize(self, steps: List[dict]) -> List[dict]:
        if self.score(steps) >= 0.8:
            return steps
        # fallback: buang langkah yang memicu konflik tinggi
        out = []
        for s in steps or []:
            t = (s.get("cmd", "") + " " + s.get("tool", "")).lower()
            if any(k in t for k in ["attack", "exploit", "troll", "harass"]):
                continue
            out.append(s)
        return out
