from typing import Dict, Any


class ValueTradeoffExplainer:
    """
    Jelasin kenapa rencana dipilih: bobot nilai, emosi moral, dampak.
    Integrasi: dipanggil dari transparency_dashboard.py untuk render.
    """

    def explain(
        self, plan: Dict[str, Any], weights: Dict[str, float], impact: Dict[str, float]
    ) -> Dict[str, Any]:
        return {
            "chosen_plan": plan.get("name", "(unnamed)"),
            "weights": weights,
            "impact_scores": impact,
            "why": [
                "Plan memaksimalkan manfaat manusia",
                "Risiko ketidakadilan ditekan oleh bobot 'justice_weight'",
                "Emosi moral (compassion/guilt) mengubah aversi risiko",
            ],
        }
