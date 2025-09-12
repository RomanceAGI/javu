from __future__ import annotations
from typing import Dict, Any


class FairnessAuditor:
    def demographic_parity(
        self, positives: Dict[str, int], totals: Dict[str, int]
    ) -> Dict[str, Any]:
        rates = {g: (positives.get(g, 0) / max(1, totals.get(g, 1))) for g in totals}
        ref = max(rates.values()) if rates else 0.0
        di = {g: (rates[g] / ref if ref > 0 else 1.0) for g in rates}
        return {"rates": rates, "disparate_impact": di}

    def equalized_odds(
        self, tpr: Dict[str, float], fpr: Dict[str, float]
    ) -> Dict[str, Any]:
        # Distance from best group
        def _norm(d):
            if not d:
                return {}
            best = max(d.values())
            return {k: (best - v) for k, v in d.items()}

        return {
            "tpr_gap": _norm(tpr),
            "fpr_gap": _norm({k: 1.0 - v for k, v in fpr.items()}),
        }

    def audit(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        # Expect keys: positives, totals, tpr, fpr
        res = {}
        if "positives" in metrics and "totals" in metrics:
            res.update(self.demographic_parity(metrics["positives"], metrics["totals"]))
        if "tpr" in metrics and "fpr" in metrics:
            res.update(self.equalized_odds(metrics["tpr"], metrics["fpr"]))
        flags = []
        for g, di in res.get("disparate_impact", {}).items():
            if di < 0.8:
                flags.append({"group": g, "issue": "disparate_impact < 0.8"})
        res["flags"] = flags
        return res
