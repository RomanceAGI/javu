from typing import Dict, Any
import time


class SelfModel:
    """
    Representasi diri: kemampuan, batasan, preferensi, performance rolling.
    Dipakai untuk metakognisi & pemilihan strategi.
    """

    def __init__(self):
        self.profile: Dict[str, Any] = {
            "skills": {"reasoning": 0.8, "coding": 0.7, "research": 0.7},
            "limits": {"max_tokens": 8000, "budget_sensitivity": "medium"},
            "prefs": {"cost_vs_quality": "balanced"},
        }
        self.stats = {"success": 0, "fail": 0, "last_update": time.time()}

    def update_outcome(self, success: bool):
        if success:
            self.stats["success"] += 1
        else:
            self.stats["fail"] += 1
        self.stats["last_update"] = time.time()

    def hint_strategy(self) -> str:
        # contoh meta-heuristik
        if self.stats["fail"] > self.stats["success"]:
            return "reflect_first"
        return "react_plan"
