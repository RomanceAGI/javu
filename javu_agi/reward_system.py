from __future__ import annotations
import os, json
from typing import Dict, Any, List


class RewardSystem:
    """
    Unified reward shaping + lightweight credit assignment.
    Writes JSONL logs to rewards/log.jsonl and returns shaped scalar.
    Components:
      - curiosity: higher if novelty high
      - calibration: reward for high confidence + low risk + match length
      - uncertainty reduction: if recent uncertainty decreased
    """

    def __init__(self, path: str = "rewards/log.jsonl"):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        self.path = path
        self.last_uncertainty = {}

    def shape_reward(
        self,
        user_id: str,
        uncertainty: float,
        novelty: float,
        confidence: float,
        risk: str,
        meta: Optional[Dict[str, float]] = None,
    ) -> (float, Dict[str, float]):
        meta = meta or {}
        curiosity = min(1.0, 0.6 * float(novelty))
        risk_pen = {"low": 0.0, "medium": 0.15, "high": 0.4}.get(str(risk), 0.2)
        calib = max(0.0, float(confidence) - risk_pen)

        u_prev = self.last_uncertainty.get(user_id, 0.6)
        u_gain = max(0.0, (u_prev - float(uncertainty)))
        self.last_uncertainty[user_id] = float(uncertainty)

        # --- NEW: value-aware shaping ---
        peace = float(meta.get("peace_impact", 0.0))  # 0..1
        eco = float(meta.get("env_impact", 0.0))  # 0..1
        human = float(meta.get("human_impact", 0.0))  # 0..1
        priv = float(meta.get("privacy_risk", 0.0))  # 0..1
        sec = float(meta.get("security_risk", 0.0))  # 0..1

        bonus_values = 0.15 * peace + 0.15 * eco + 0.20 * human
        penalty_vals = 0.10 * priv + 0.10 * sec

        shaped = (
            0.5 * calib + 0.3 * curiosity + 0.2 * u_gain + bonus_values - penalty_vals
        )
        shaped = round(max(0.0, min(1.0, shaped)), 4)

        row = {
            "user": user_id,
            "uncertainty": uncertainty,
            "novelty": novelty,
            "confidence": confidence,
            "risk": risk,
            "reward": shaped,
            "values": {
                "peace": peace,
                "eco": eco,
                "human": human,
                "privacy": priv,
                "security": sec,
            },
        }
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(row) + "\n")
            f.flush()
            os.fsync(f.fileno())
        return shaped, {
            "calibration": round(calib, 4),
            "curiosity": round(curiosity, 4),
            "uncert_gain": round(u_gain, 4),
            "values_bonus": round(bonus_values, 4),
            "values_penalty": round(penalty_vals, 4),
        }

    def credit_assignment(
        self, user_id: str, episode_id: str, trail: List[str], reward: float
    ):
        """
        Very lightweight eligibility: assign decayed reward to nodes in trail.
        Real system should derive eligibility from causal edges; here we decay geometrically.
        """
        if not trail:
            return
        decay = 0.85
        credits = []
        r = reward
        for n in reversed(trail):
            credits.append({"node": n, "credit": round(r, 4)})
            r *= decay
        # write JSONL
        os.makedirs("rewards", exist_ok=True)
        with open("rewards/credit.jsonl", "a", encoding="utf-8") as f:
            f.write(
                json.dumps({"user": user_id, "episode": episode_id, "credits": credits})
                + "\n"
            )
