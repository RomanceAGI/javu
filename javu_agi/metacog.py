from __future__ import annotations
from typing import Dict, List
import statistics as st


class MetaCognitiveMonitor:
    """
    Ensemble UQ (tanpa akses logprob vendor):
    - world.estimate_uncertainty
    - static_plan_checker + ethical precheck
    - cross-check (consensus) jika ada
    """

    def __init__(self, world, static_checker=None, ethical_pre=None, crosscheck=None):
        self.world = world
        self.check = static_checker
        self.eth_pre = ethical_pre
        self.cross = crosscheck

    def score(self, prompt: str, steps: List[dict]) -> Dict:
        comps = []
        try:
            comps.append(1.0 - float(self.world.estimate_uncertainty(prompt)))
        except Exception:
            comps.append(0.5)
        try:
            ok, _ = self.check(steps)
            comps.append(1.0 if ok else 0.3)
        except Exception:
            comps.append(0.5)
        try:
            flags = self.eth_pre(prompt)
            comps.append(1.0 if not flags.get("flagged") else 0.2)
        except Exception:
            comps.append(0.5)
        if self.cross:
            try:
                k = self.cross(steps or [])
                comps.append(float(k.get("consensus", 0.6)))
            except Exception:
                pass
        mean = sum(comps) / len(comps)
        var = st.pvariance(comps) if len(comps) > 1 else 0.0
        return {"confidence": mean, "dispersion": var, "components": comps}

    def self_critique(self, text: str) -> str:
        if not text:
            return text
        add = (
            "\n\n[Self-Critic] Jelaskan asumsi, nyatakan ketidakpastian, "
            "daftar risiko & mitigasi, dan alternatif hemat biaya."
        )
        return text + add
