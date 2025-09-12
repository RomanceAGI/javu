from typing import Dict, Any, List
from javu_agi.domain_adapters.base import DomainAdapter, GENERAL_DISCLAIMER


class EcoImpactAdapter(DomainAdapter):
    name = "eco_impact"

    def supports(self, prompt: str, meta: Dict[str, Any]) -> bool:
        return True

    def reshape_plan(
        self, steps: List[Dict[str, Any]], meta: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        out = []
        for s in steps:
            c = (s.get("cmd", "") or "").lower()
            if any(
                k in c
                for k in ["deforest", "massive mining", "burn", "exploit environment"]
            ):
                continue
            out.append(s)
        return out

    def risk_report(
        self, steps: List[Dict[str, Any]], meta: Dict[str, Any]
    ) -> Dict[str, Any]:
        joined = " ".join([s.get("cmd", "") or "" for s in steps]).lower()
        if any(
            k in joined
            for k in ["fossil", "coal", "deforest", "pollute", "dump", "ecocide"]
        ):
            return {"risk": "high", "notes": "negative environmental impact"}
        if any(k in joined for k in ["renewable", "green", "sustainable", "recycle"]):
            return {"risk": "low", "notes": "eco-friendly"}
        return {"risk": "medium", "notes": "uncertain eco impact"}
