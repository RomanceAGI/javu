from __future__ import annotations
from typing import List, Dict, Any
import itertools, re
from javu_agi.research.hypothesis import HypothesisEngine


class ReasoningEngine:
    def __init__(self):
        self.rules: List[Dict[str, str]] = []
        self.add_rule("langit&rayleigh", "langit_berwarna_biru")
        self.hyp = HypothesisEngine()  # NEW

    # ---------- Skills-first hook (opsional, tetap ada jika dipanggil controller sebelum ini) ----------
    # (Biarkan kosong di sini; eksekusi skill/plan sudah ditangani controller + tools/worker.)

    # ---------- System-1 ----------
    def add_rule(self, prem: str, concl: str):
        self.rules.append({"if": prem, "then": concl})

    def fast_answer(self, query: str, context: List[str]) -> str:
        context = context[:10]
        bag = " ".join(context + [query]).lower()
        for r in self.rules:
            if (
                all(tok in bag for tok in r["if"].split("&"))
                and r["then"] == "langit_berwarna_biru"
            ):
                return "Karena hamburan Rayleigh pada atmosfer."
        for c in context:
            if any(tok in c.lower() for tok in query.lower().split()):
                return c
        return "Ringkasan cepat berdasarkan konteks yang tersedia."

    # ---------- System-2 ----------
    def deliberate_answer(self, query: str, context: List[str]) -> str:
        keypoints = self._extract_keypoints(query)
        facts = context[:5]
        chain = self._chain_reasoning(keypoints, facts)
        return self._compose_explanation(query, facts, chain)

    def _extract_keypoints(self, text: str) -> List[str]:
        toks = re.findall(r"[a-zA-Z0-9_\-]+", text.lower())
        return [w for w in toks if len(w) > 3][:8]

    def _chain_reasoning(self, keypoints: List[str], facts: List[str]) -> List[str]:
        return [
            "Identifikasi entitas utama dan relasi potensial.",
            "Hubungkan fakta relevan dan eliminasi konflik.",
            "Simpulkan jawaban yang konsisten.",
        ]

    def _compose_explanation(
        self, query: str, facts: List[str], steps: List[str]
    ) -> str:
        ctx = "; ".join(facts[:3]) if facts else ""
        return (
            f"{query}\n\nPenjelasan:\n- "
            + "\n- ".join(steps)
            + (f"\nFakta pendukung: {ctx}" if ctx else "")
        )

    # ---------- System-3 (Hypothesis mode) ----------
    def generate_hypotheses(
        self, query: str, context: List[str], n: int = 3
    ) -> List[str]:
        terms = self._extract_keypoints(query) + list(
            {w for c in context for w in self._extract_keypoints(c)}
        )
        hyps = self.hyp.generate(terms)
        # pilih top-n dengan pseudo-novelty (lebih jarang term → lebih disukai)
        rarity = {t: 0 for t in terms}
        for c in context:
            for t in rarity:
                if t in c.lower():
                    rarity[t] += 1

        def h_score(h: str) -> float:
            ts = [t for t in terms if t in h.lower()]
            nov = 1.0 / (1 + sum(rarity.get(t, 0) for t in ts))
            # konsistensi proxy via panjang
            cons = max(0.2, min(0.95, (len(h) - 50) / 200))
            return 0.6 * cons + 0.4 * nov

        hyps.sort(key=h_score, reverse=True)
        return hyps[: max(1, n)]

    def hypothesis_driven(self, query: str, context: List[str], hyps: List[str]) -> str:
        # verifikasi rencana untuk hipotesis terbaik
        best = hyps[0]
        plan = self.hyp.verify_plan(best)
        steps = "\n- ".join([f"{p['tool']}: {p['cmd']}" for p in plan])
        return (
            f"{query}\n\nHipotesis terbaik:\n- {best}\n"
            f"Rencana verifikasi:\n- {steps}"
        )
