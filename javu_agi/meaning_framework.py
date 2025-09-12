from __future__ import annotations
from typing import Dict, Any, List


class MeaningFramework:
    def evaluate(self, plan: List[Dict[str, Any]]) -> Dict[str, Any]:
        text = " ".join(map(str, plan)).lower()
        dignity = (
            1.0
            if all(k not in text for k in ["demean", "dehumanize", "humiliate"])
            else 0.2
        )
        wellbeing = 0.6 + 0.2 * ("health" in text or "safety" in text)
        purpose = 0.5 + 0.3 * ("education" in text or "create" in text)
        compassion = 0.5 + 0.3 * ("help" in text or "care" in text)
        score = max(0.0, min(1.0, 0.25 * (dignity + wellbeing + purpose + compassion)))
        return {
            "dignity": round(dignity, 3),
            "wellbeing": round(wellbeing, 3),
            "purpose": round(purpose, 3),
            "compassion": round(compassion, 3),
            "meaning_score": round(score, 3),
        }
