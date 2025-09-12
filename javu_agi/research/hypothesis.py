from __future__ import annotations
from typing import List, Dict
import itertools, math


class HypothesisEngine:
    """
    Generator & evaluator ringan untuk hipotesis ilmiah.
    - Generate pasangan variabel & mekanisme laten
    - Skor kelayakan (proxy) via konsistensi logis sederhana + novelty
    """

    def generate(self, terms: List[str], k: int = 5) -> List[str]:
        terms = list(dict.fromkeys([t for t in terms if len(t) > 3]))[:10]
        hyps = []
        for a, b in itertools.combinations(terms[:6], 2):
            hyps.append(f"Hipotesis: {a} mempengaruhi {b} via mekanisme laten M.")
            if len(hyps) >= k:
                break
        if not hyps:
            hyps = ["Hipotesis: terdapat variabel laten yang menjelaskan fenomena."]
        return hyps

    def score(self, hypothesis: str, novelty: float, consistency: float) -> float:
        # proxy: bobot novelty+consistency
        return round(0.6 * consistency + 0.4 * novelty, 3)

    def evaluate_set(self, hyps: List[str], novelty: float) -> Dict[str, float]:
        # konsistensi proxy: penalti jika terlalu generik/pendek
        scores = {}
        for h in hyps:
            L = len(h)
            cons = max(0.2, min(0.95, (L - 50) / 200))
            scores[h] = self.score(h, novelty, cons)
        return scores
