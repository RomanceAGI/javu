from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any, List


@dataclass
class PersonModel:
    role: str
    knowledge: float = 0.5
    consent: float = 0.5
    wellbeing: float = 0.7


class EmpathyModel:
    def __init__(self):
        pass

    def assess(
        self, plan: List[Dict[str, Any]], actors: List[PersonModel]
    ) -> Dict[str, Any]:
        text = " ".join(map(str, plan)).lower()
        harm = 0.0
        if "leak" in text or "pii" in text or "surveil" in text:
            harm += 0.6
        if "stress" in text or "overwork" in text:
            harm += 0.3
        consent_needed = any(a.consent < 0.5 for a in actors)
        recs = []
        if consent_needed:
            recs.append("Dapatkan persetujuan eksplisit dan opsi opt-out.")
        if harm > 0.5:
            recs.append("Kurangi pengumpulan data; gunakan agregasi/anonimisasi.")
        return {
            "harm": min(1.0, harm),
            "recommendations": recs,
            "actors": [a.__dict__ for a in actors],
        }
