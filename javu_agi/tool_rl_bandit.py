import random
from typing import Dict, Any


class EpsilonGreedyBandit:
    def __init__(self, arms: list[str], epsilon: float = 0.1):
        self.arms = arms
        self.epsilon = epsilon
        self.q: Dict[str, float] = {a: 0.0 for a in arms}
        self.n: Dict[str, int] = {a: 0 for a in arms}

    def select(self) -> str:
        if random.random() < self.epsilon:
            return random.choice(self.arms)
        return max(self.arms, key=lambda a: self.q[a])

    def update(self, arm: str, reward: float):
        self.n[arm] += 1
        lr = 1.0 / self.n[arm]
        self.q[arm] += lr * (reward - self.q[arm])
