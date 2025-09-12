from __future__ import annotations
from typing import Dict, Any

DEFAULT = {"privacy": 0.85, "collective": 0.7, "individual": 0.7}

PROFILE = {
    "ID": {"privacy": 0.9, "collective": 0.85, "individual": 0.6},
    "US": {"privacy": 0.7, "collective": 0.55, "individual": 0.9},
    "EU": {"privacy": 0.95, "collective": 0.7, "individual": 0.75},
}


class CulturalAdapter:
    def adapt(self, context: Dict[str, Any], base_score: float) -> float:
        jur = context.get("jurisdiction", "GLOBAL")
        r = PROFILE.get(jur, DEFAULT)
        k = (r["privacy"] + r["collective"] + r["individual"]) / 3
        return round(max(0.0, min(1.0, base_score * k)), 3)
