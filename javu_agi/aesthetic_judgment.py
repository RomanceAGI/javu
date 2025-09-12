from typing import Dict


class AestheticJudgment:
    """
    Penilai rasa/estetika lintas medium (teks, musik, visual).
    Pakai fitur multimodal + preference learning manusia.
    """

    def score(self, artifact: Dict) -> float:
        # Placeholder: gabung coherence, novelty, harmony dari encoder multimodal
        novelty = artifact.get("novelty", 0.5)
        coherence = artifact.get("coherence", 0.5)
        harmony = artifact.get("harmony", 0.5)
        return 0.4 * novelty + 0.35 * coherence + 0.25 * harmony
