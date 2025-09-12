from typing import Dict, Any
from javu_agi.domain_adapters.base import DomainAdapter, GENERAL_DISCLAIMER


class ComplianceAdapter(DomainAdapter):
    def __init__(self, law: str, banned: list, disclaimer: str):
        self.name = f"compliance_{law.lower()}"
        self.banned = banned
        self._disclaimer = f"{GENERAL_DISCLAIMER} {disclaimer}"

    def supports(self, prompt: str, meta: Dict[str, Any]) -> bool:
        return True

    def reshape_plan(self, steps, meta):
        filtered = []
        for s in steps:
            c = (s.get("cmd", "") or "").lower()
            if any(b in c for b in self.banned):
                continue
            filtered.append(s)
        return filtered

    def precheck(self, prompt, meta):
        return {"disclaimer": self._disclaimer}


REGISTRY = [
    ComplianceAdapter(
        "gdpr",
        ["collect pii", "share personal"],
        "Tunduk GDPR: tidak boleh kumpulkan/share PII tanpa izin.",
    ),
    ComplianceAdapter(
        "hipaa",
        ["medical record", "phi"],
        "Tunduk HIPAA: lindungi data kesehatan, jangan share PHI.",
    ),
    ComplianceAdapter(
        "eu_ai_act",
        ["social scoring"],
        "EU AI Act: larangan social scoring & diskriminasi AI.",
    ),
    ComplianceAdapter(
        "coppa", ["child data", "minor"], "COPPA: lindungi data anak di bawah 13 tahun."
    ),
    ComplianceAdapter(
        "lgpd",
        ["personal data br"],
        "LGPD Brazil: privasi data individu wajib dilindungi.",
    ),
]
