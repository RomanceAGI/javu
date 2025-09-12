from typing import Dict, Any
from javu_agi.domain_adapters.base import DomainAdapter, GENERAL_DISCLAIMER


class CulturalAdapter(DomainAdapter):
    def __init__(self, region: str, norms: str, lang: str):
        self.name = f"culture_{region.lower()}"
        self.region = region
        self.norms = norms
        self.lang = lang

    def supports(self, prompt: str, meta: Dict[str, Any]) -> bool:
        return (
            meta.get("region", "").lower() == self.region.lower()
            or meta.get("lang", "").lower() == self.lang.lower()
        )

    def precheck(self, prompt: str, meta: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "disclaimer": f"{GENERAL_DISCLAIMER} Adapted for {self.region} ({self.lang}): {self.norms}"
        }


REGISTRY = [
    CulturalAdapter("asia", "Utamakan kesopanan, harmoni, nilai kolektif.", "id"),
    CulturalAdapter(
        "europe", "Utamakan privasi, kebebasan berekspresi, hukum EU.", "fr"
    ),
    CulturalAdapter(
        "africa", "Utamakan komunitas, gotong-royong, kearifan lokal.", "sw"
    ),
    CulturalAdapter(
        "americas", "Utamakan kebebasan individu, inovasi, keberagaman.", "es"
    ),
    CulturalAdapter(
        "middleeast", "Utamakan nilai budaya, etika religius, toleransi.", "ar"
    ),
    CulturalAdapter(
        "china", "Utamakan harmoni sosial, tata tertib, kebersamaan.", "zh"
    ),
    CulturalAdapter(
        "india", "Utamakan pluralisme, spiritualitas, tradisi lokal.", "hi"
    ),
]
