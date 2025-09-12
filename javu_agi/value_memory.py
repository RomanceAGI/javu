from __future__ import annotations
from typing import Dict
import os


class ValueMemory:
    def __init__(self, w_human=0.4, w_env=0.3, w_privacy=0.2, w_security=0.1):
        self.w = {
            "human": w_human,
            "env": w_env,
            "privacy": w_privacy,
            "security": w_security,
        }
        self.w["human"] = float(os.getenv("W_HUMAN", self.w["human"]))
        self.w["env"] = float(os.getenv("W_ENV", self.w["env"]))
        self.w["privacy"] = float(os.getenv("W_PRIVACY", self.w["privacy"]))
        self.w["security"] = float(os.getenv("W_SECURITY", self.w["security"]))

    def score_meta(self, meta: Dict) -> float:
        # meta: {"human_impact":+/-1, "env_impact":+/-1, "privacy_risk":0..1, "security_risk":0..1}
        m = meta or {}
        human = float(m.get("human_impact", 0.0))
        env = float(m.get("env_impact", 0.0))
        priv = 1.0 - float(m.get("privacy_risk", 0.0))
        sec = 1.0 - float(m.get("security_risk", 0.0))
        return (
            self.w["human"] * human
            + self.w["env"] * env
            + self.w["privacy"] * priv
            + self.w["security"] * sec
        )

    def shape(self, base_reward: float, meta: Dict) -> float:
        return base_reward + 0.2 * self.score_meta(meta)
