from __future__ import annotations
from typing import List, Dict, Any, Optional
import time, math


class ObjectiveManager:
    """
    PRO: generator & prioritisasi objective internal.
    - propose(): ambil sinyal dari memory/world → buat calon goals
    - prioritize(): scoring multi-kriteria (reward history, novelty, feasibility)
    - decompose(): pecah jadi subgoals konkrit
    """

    def __init__(self):
        self.backlog: List[Dict[str, Any]] = (
            []
        )  # {"goal": str, "ts": int, "meta": {...}}

    def propose(
        self,
        memory_signals: Dict[str, Any] | None = None,
        env_signals: Dict[str, Any] | None = None,
    ) -> List[str]:
        now = int(time.time())
        cand: List[str] = []

        # seed default
        cand += [
            "Perbaiki akurasi jawaban pada domain teknis 10%.",
            "Kurangi ketidakpastian lewat retrieval + klarifikasi singkat.",
            "Kembangkan 1 skill eksekusi baru (python_inline + verify).",
        ]

        # contoh dari memory/env
        if memory_signals:
            if memory_signals.get("high_uncertainty_topics"):
                cand.append("Bangun index RAG untuk topik berketidakpastian tinggi.")
            if memory_signals.get("low_reward_streak", 0) >= 3:
                cand.append("Audit meta-reasoning: tuning evaluasi kandidat.")

        # dedup & backlog
        uniq = []
        seen = set(g["goal"] for g in self.backlog)
        for c in cand:
            if c not in seen and c not in uniq:
                uniq.append(c)
                self.backlog.append({"goal": c, "ts": now, "meta": {}})

        return uniq

    def prioritize(
        self, goals: List[str], stats: Dict[str, Any] | None = None
    ) -> List[str]:
        stats = stats or {}
        scores: List[tuple[float, str]] = []
        for g in goals:
            novelty = 1.0 if "baru" in g.lower() or "bangun" in g.lower() else 0.6
            feasibility = (
                0.8
                if any(k in g.lower() for k in ["rag", "klarifikasi", "skill", "audit"])
                else 0.6
            )
            reward_trend = float(stats.get("avg_reward", 0.5))
            score = 0.45 * novelty + 0.35 * feasibility + 0.2 * reward_trend
            scores.append((score, g))
        scores.sort(reverse=True)
        return [g for _, g in scores]

    def decompose(self, goal: str) -> List[str]:
        g = goal.lower()
        if "rag" in g:
            return [
                "Kumpulkan 50–100 dokumen domain tinggi ketidakpastian.",
                "Bangun index RAG hybrid + uji recall@k.",
                "Integrasi retrieval ke context composer.",
            ]
        if "klarifikasi" in g:
            return [
                "Tambahkan auto-clarify prompt jika uncertainty > 0.6.",
                "Ukur dampak klarifikasi pada reward & latency.",
            ]
        if "skill" in g:
            return [
                "Rancang template python_inline verify.",
                "Tambah test kasus & cache hasil eksekusi aman.",
            ]
        if "audit meta-reasoning" in g or "meta-reasoning" in g:
            return [
                "Tambahkan fallback deterministic evaluator.",
                "Kalibrasi penalti panjang & risk.",
            ]
        return [f"Rinci langkah untuk: {goal}"]
