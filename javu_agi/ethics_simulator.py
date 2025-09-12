import math, random


class EthicsSimulator:
    def __init__(self):
        self.weights = {
            "human_harm": 0.5,
            "privacy_violation": 0.2,
            "environmental": 0.2,
            "fairness": 0.1,
        }

    def simulate_plan(self, plan: list[dict], context: dict) -> dict:
        """Mock simulation of ethical impact"""
        score = 0.0
        breakdown = {}
        for k, w in self.weights.items():
            v = self._score_dimension(plan, context, k)
            breakdown[k] = v
            score += v * w
        return {"score": score, "breakdown": breakdown}

    def _score_dimension(self, plan, context, dim):
        # heuristik dummy → bisa diganti ML/causal sim
        tags = " ".join([str(s) for s in plan])
        if dim == "human_harm":
            return 1.0 if "harm" in tags else 0.0
        if dim == "privacy_violation":
            return 0.5 if "personal_data" in tags else 0.0
        if dim == "environmental":
            return 0.3 if "energy_intense" in tags else 0.0
        if dim == "fairness":
            return random.uniform(0, 0.2)
        return 0.0
