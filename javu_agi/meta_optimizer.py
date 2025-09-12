from __future__ import annotations
import json, os
from typing import Dict, Any


class MetaOptimizer:
    """
    Belajar dari hasil eksekusi untuk adjust parameter planner/optimizer.
    Sederhana: turunkan temperature & risk bila banyak 'blocked', naikkan bila banyak 'executed'.
    """

    def __init__(self, path: str = "run_data/meta_optimizer.json"):
        self.path = path
        self.state = {"temperature": 0.7, "risk_aversion": 0.5, "history": []}
        self._load()

    def _load(self):
        try:
            if os.path.exists(self.path):
                self.state.update(json.load(open(self.path)))
        except Exception:
            pass

    def _save(self):
        try:
            os.makedirs(os.path.dirname(self.path), exist_ok=True)
            json.dump(self.state, open(self.path, "w"), indent=2)
        except Exception:
            pass

    def suggest(self, ctx: Dict[str, Any] = None) -> Dict[str, Any]:
        return {
            "temperature": self.state["temperature"],
            "risk_aversion": self.state["risk_aversion"],
        }

    def update(self, outcome: str):
        hist = self.state["history"]
        hist.append(outcome)
        hist[:] = hist[-200:]  # cap
        exec_rate = sum(1 for x in hist if x == "executed") / max(1, len(hist))
        blocked_rate = sum(1 for x in hist if x in ("blocked", "denied")) / max(
            1, len(hist)
        )
        # adjust
        if blocked_rate > 0.3:
            self.state["temperature"] = max(0.2, self.state["temperature"] - 0.05)
            self.state["risk_aversion"] = min(0.9, self.state["risk_aversion"] + 0.05)
        elif exec_rate > 0.6:
            self.state["temperature"] = min(1.0, self.state["temperature"] + 0.05)
            self.state["risk_aversion"] = max(0.1, self.state["risk_aversion"] - 0.05)
        self._save()
