from __future__ import annotations
from typing import Dict, List


class ToM:
    """
    Model kepercayaan sederhana per stakeholder -> prediksi reaksi.
    Tidak melatih LLM; state disimpan di memori internal.
    """

    def __init__(self, memory):
        self.memory = memory

    def update(self, name: str, observation: Dict):
        key = f"tom:{name}"
        state = self.memory.load(key) or {"beliefs": {}, "goals": {}, "tolerance": 0.7}
        state["beliefs"].update(observation.get("beliefs", {}))
        state["goals"].update(observation.get("goals", {}))
        self.memory.store(key, state)

    def predict_reaction(
        self, plan_steps: List[dict], stakeholders: List[str]
    ) -> Dict[str, float]:
        out = {}
        for s in stakeholders or []:
            st = self.memory.load(f"tom:{s}") or {"tolerance": 0.7}
            tol = float(st.get("tolerance", 0.7))
            risk = 0.0
            for step in plan_steps or []:
                cmd = (step.get("cmd") or "").lower()
                if any(
                    k in cmd for k in ["delete", "kill", "ddos", "exploit", "breach"]
                ):
                    risk += 0.6
                if any(k in cmd for k in ["track", "collect", "upload", "share"]):
                    risk += 0.2
            val = max(0.0, min(1.0, tol - risk))
            out[s] = val
        return out  # 0..1 approval likelihood
