from __future__ import annotations
import math, random
from typing import Dict, Any, List


class LinUCB:
    def __init__(self, dim: int = 8, alpha: float = 0.7):
        self.dim, self.alpha = dim, alpha
        self.A = {}
        self.b = {}

    def _z(self, x: List[float]) -> List[float]:
        x = (x or [])[: self.dim] + [0.0] * max(0, self.dim - len(x or []))
        return x

    def _theta(self, arm: str) -> List[float]:
        A = self.A.setdefault(
            arm,
            [
                [1.0 if i == j else 0.0 for j in range(self.dim)]
                for i in range(self.dim)
            ],
        )
        b = self.b.setdefault(arm, [0.0] * self.dim)
        # solve A^{-1} b by Gauss-Seidel sederhana (dim kecil)
        x = [0.0] * self.dim
        for _ in range(20):
            for i in range(self.dim):
                s = b[i] - sum(A[i][j] * x[j] for j in range(self.dim) if j != i)
                x[i] = s / A[i][i]
        return x

    def select(self, arms: List[str], ctx: List[float]) -> str:
        if not arms:
            return ""
        z = self._z(ctx)
        best, score = arms[0], float("-inf")
        for a in arms:
            theta = self._theta(a)
            mu = sum(ti * zi for ti, zi in zip(theta, z))
            # crude uncertainty term: diag(A)^{-1}
            A = self.A[a]
            inv_diag = sum(1.0 / A[i][i] for i in range(self.dim)) / self.dim
            ucb = mu + self.alpha * math.sqrt(inv_diag)
            if ucb > score:
                score, best = ucb, a
        return best

    def update(self, arm: str, ctx: List[float], reward: float):
        z = self._z(ctx)
        A = self.A.setdefault(
            arm,
            [
                [1.0 if i == j else 0.0 for j in range(self.dim)]
                for i in range(self.dim)
            ],
        )
        b = self.b.setdefault(arm, [0.0] * self.dim)
        # rank-1 update
        for i in range(self.dim):
            for j in range(self.dim):
                A[i][j] += z[i] * z[j]
        for i in range(self.dim):
            b[i] += reward * z[i]


class MetaPolicy:
    def __init__(self, dim: int = 8, alpha0: float = 0.6, ewma: float = 0.2):
        self.dim = dim
        self.alpha0 = alpha0
        self.ewma = ewma
        self.r_ewma: Dict[str, float] = {"S1": 0.0, "S2": 0.0, "S3": 0.0}
        self.n: Dict[str, int] = {"S1": 0, "S2": 0, "S3": 0}

    def choose_mode(self, context_vec: List[float]) -> str:
        t = sum(self.n.values()) + 1
        alpha = self.alpha0 / math.sqrt(max(1, t / 10))
        best, score = "S2", float("-inf")
        for m in ("S1", "S2", "S3"):
            mean = self.r_ewma[m]
            bonus = alpha * math.sqrt(1.0 / max(1, self.n[m]))
            s = mean + bonus
            if s > score:
                score, best = s, m
        return best

    def record(
        self, mode: str, context_vec: List[float], reward: float, metrics_cb=None
    ):
        m = mode if mode in self.r_ewma else "S2"
        self.n[m] += 1
        self.r_ewma[m] = (1 - self.ewma) * self.r_ewma[m] + self.ewma * float(reward)
        if metrics_cb:
            try:
                metrics_cb("meta_reward", {"mode": m}, float(reward))
                metrics_cb("meta_ewma", {"mode": m}, self.r_ewma[m])
            except Exception:
                pass
