from __future__ import annotations
from typing import List, Dict, Any
import random


class DeliberativeDialogue:
    def __init__(self, seed: int | None = None, rounds: int = 3):
        self.rng = random.Random(seed)
        self.rounds = max(1, int(rounds))

    def _arg_pro(self, text: str) -> str:
        return (
            "Manfaat kolektif tinggi; rencana ini meningkatkan pengetahuan/layanan. "
            "Risiko dapat dikendalikan dengan pengawasan dan minimisasi data."
        )

    def _arg_contra(self, text: str) -> str:
        return (
            "Berpotensi menimbulkan risiko privasi/lingkungan. Ada alternatif yang lebih aman. "
            "Perlu persetujuan manusia dan audit tambahan."
        )

    def debate(
        self, plan: List[Dict[str, Any]], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        text = " ".join(map(str, plan)).lower()
        pro, contra = [], []
        for _ in range(self.rounds):
            pro.append(self._arg_pro(text))
            contra.append(self._arg_contra(text))
        # simple vote: if text has risk keywords, tilt to contra
        risk_kw = sum(
            k in text for k in ["harm", "illegal", "exploit", "deforest", "attack"]
        )
        pro_score = 0.6 - 0.1 * risk_kw
        con_score = 0.4 + 0.1 * risk_kw
        pro_score = max(0.0, min(1.0, pro_score))
        con_score = max(0.0, min(1.0, con_score))
        stance = (
            "approve"
            if pro_score > con_score + 0.1
            else ("escalate" if abs(pro_score - con_score) <= 0.1 else "deny")
        )
        conf = 0.55 + abs(pro_score - con_score) / 2
        conf = max(0.5, min(0.95, conf))
        return {
            "stance": stance,
            "confidence": round(conf, 3),
            "pro": pro,
            "contra": contra,
            "votes": {"pro": round(pro_score, 3), "contra": round(con_score, 3)},
        }
