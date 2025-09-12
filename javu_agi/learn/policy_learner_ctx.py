from __future__ import annotations
from typing import Dict, List
import json, os
import numpy as np

ARMS = ["S1", "S2", "S3"]


class ContextualPolicyLearner:
    """
    LinUCB per-arm (S1/S2/S3) dengan regularisasi.
    Feature vector x (d-dim) → reward scalar r \in [0,1].
    Persist ke file JSON; cocok buat streaming updates.
    """

    def __init__(
        self,
        path: str = "rewards/policy_ctx.json",
        dim: int = 8,
        alpha: float = 0.8,
        l2: float = 1e-2,
    ):
        self.path = path
        self.dim = dim
        self.alpha = alpha
        self.l2 = l2
        os.makedirs(os.path.dirname(path), exist_ok=True)
        self._load()

    def _zeros(self):
        A = np.eye(self.dim) * self.l2  # dxd
        b = np.zeros((self.dim, 1))  # dx1
        return A, b

    def _load(self):
        if os.path.exists(self.path):
            raw = json.load(open(self.path, "r"))
            self.A = {a: np.array(raw["A"][a]) for a in ARMS}
            self.b = {a: np.array(raw["b"][a]) for a in ARMS}
        else:
            self.A = {a: self._zeros()[0] for a in ARMS}
            self.b = {a: self._zeros()[1] for a in ARMS}

    def _save(self):
        json.dump(
            {
                "A": {a: self.A[a].tolist() for a in ARMS},
                "b": {a: self.b[a].tolist() for a in ARMS},
            },
            open(self.path, "w"),
            indent=2,
        )

    def _theta(self, arm: str):
        # theta = A^{-1} b
        Ainv = np.linalg.inv(self.A[arm])
        return Ainv @ self.b[arm], Ainv

    def choose(self, x: List[float]) -> Dict:
        # LinUCB: p = theta^T x + alpha * sqrt(x^T A^{-1} x)
        x = np.array(x, dtype=float).reshape(-1, 1)
        scores = {}
        for a in ARMS:
            theta, Ainv = self._theta(a)
            mean = float((theta.T @ x)[0, 0])
            bonus = float(np.sqrt(x.T @ Ainv @ x)[0, 0])
            scores[a] = mean + self.alpha * bonus
        arm = max(scores.items(), key=lambda kv: kv[1])[0]
        return {"arm": arm, "scores": scores}

    def record(self, arm: str, x: List[float], r: float):
        x = np.array(x, dtype=float).reshape(-1, 1)
        self.A[arm] += x @ x.T
        self.b[arm] += r * x
        self._save()
