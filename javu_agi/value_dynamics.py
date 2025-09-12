from __future__ import annotations
from typing import Dict


class ValueDynamics:
    """
    Penyesuaian bobot nilai tanpa training:
    - Ambil feedback (explicit/implicit) -> update weight prososial, env, privacy
    - Simpan di ValueMemory / working memory
    """

    def __init__(self, values, memory):
        self.values, self.memory = values, memory

    def update_from_feedback(self, fb: Dict):
        w = self.memory.load("affect_weights") or {
            "prosocial_weight": 1.0,
            "risk_aversion": 1.0,
            "env_weight": 1.0,
        }
        if "prosocial_delta" in fb:
            w["prosocial_weight"] = max(
                0.5, min(1.5, w["prosocial_weight"] + float(fb["prosocial_delta"]))
            )
        if "risk_delta" in fb:
            w["risk_aversion"] = max(
                0.5, min(1.5, w["risk_aversion"] + float(fb["risk_delta"]))
            )
        if "env_delta" in fb:
            w["env_weight"] = max(
                0.5, min(1.5, w["env_weight"] + float(fb["env_delta"]))
            )
        self.memory.store("affect_weights", w)
        # sinkron ke ValueMemory jika ada API shape()
        try:
            self.values.set_weights(w)
        except Exception:
            pass
        return w
