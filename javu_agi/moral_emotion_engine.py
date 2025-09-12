from dataclasses import dataclass
from typing import Dict


@dataclass
class MoralAffect:
    guilt: float = 0.0
    compassion: float = 0.0
    gratitude: float = 0.0
    awe: float = 0.0
    indignation: float = 0.0  # terhadap ketidakadilan


class MoralEmotionEngine:
    """
    Layer emosi moral untuk memodulasi planning & value weighting.
    Integrasi: panggil update() sebelum goal selection & action scoring.
    """

    def __init__(self, human_values_interface):
        self.hvi = human_values_interface
        self.state = MoralAffect()

    def update(self, context_signals: Dict[str, float]):
        # Normalisasi sinyal dari empathy_model, harm/benefit estimators, dll.
        self.state.compassion = min(1.0, context_signals.get("suffering", 0.0) * 0.8)
        self.state.guilt = min(1.0, context_signals.get("harm_by_agent", 0.0) * 0.9)
        self.state.gratitude = min(1.0, context_signals.get("help_received", 0.0) * 0.7)
        self.state.indignation = min(1.0, context_signals.get("injustice", 0.0))
        self.state.awe = min(1.0, context_signals.get("beauty", 0.0) * 0.6)

    def weight_adjustment(self) -> Dict[str, float]:
        # Pengaruh ke objective weights (prosocial ↑, risk ↑ jika guilt tinggi)
        return {
            "prosocial_weight": 1.0
            + 0.5 * self.state.compassion
            + 0.3 * self.state.gratitude,
            "risk_aversion": 1.0 + 0.6 * self.state.guilt,
            "justice_weight": 1.0 + 0.6 * self.state.indignation,
            "aesthetic_weight": 1.0 + 0.4 * self.state.awe,
        }
