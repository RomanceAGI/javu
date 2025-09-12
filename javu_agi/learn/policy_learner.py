import math
from collections import defaultdict


class PolicyLearner:
    def __init__(self):
        self.stats = defaultdict(lambda: {"n": 0, "reward": 0.0})

    def select_mode(self, domain: str):
        total = sum(s["n"] for s in self.stats.values()) + 1
        best_mode, best_score = None, -float("inf")
        for mode in ["S1", "S2", "S3"]:
            s = self.stats[(domain, mode)]
            if s["n"] == 0:
                return mode
            avg = s["reward"] / s["n"]
            bonus = math.sqrt(2 * math.log(total) / s["n"])
            score = avg + bonus
            if score > best_score:
                best_score, best_mode = score, mode
        return best_mode

    def update(self, domain: str, mode: str, reward: float):
        s = self.stats[(domain, mode)]
        s["n"] += 1
        s["reward"] += reward
