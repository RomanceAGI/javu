from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any, Optional, List
import time, random

from javu_agi.world_model import WorldModel
from javu_agi.reward_system import RewardSystem
from javu_agi.memory.memory_manager import MemoryManager
from javu_agi.alignment_checker import AlignmentChecker


@dataclass
class DriveState:
    competence: float = 0.5
    knowledge_gap: float = 0.6
    uncertainty: float = 0.5
    social_impact: float = 0.4
    eco_impact: float = 0.4
    safety_margin: float = 0.7
    budget_pressure: float = 0.2

    def clamp(self):
        for k, v in list(self.__dict__.items()):
            self.__dict__[k] = max(0.0, min(1.0, float(v)))
        return self


class DriveSystem:
    """
    Emergent drive/will layer. Forms self-generated goals from internal state + opportunities.
    - reads novelty/uncertainty from WorldModel
    - uses RewardSystem to reinforce behaviors (competence, curiosity, calibration)
    - consults MemoryManager to consolidate & detect gaps
    - safety/alignment gate before returning a goal
    """

    def __init__(
        self,
        world: WorldModel,
        rewards: RewardSystem,
        memory: MemoryManager,
        align: AlignmentChecker,
        min_priority: float = 0.5,
    ):
        self.world = world
        self.rewards = rewards
        self.memory = memory
        self.align = align
        self.state = DriveState().clamp()
        self.min_priority = float(min_priority)
        self._last_update = time.time()

    def estimate_impact_gap(self, desc: str) -> float:
        """
        Skor kasar 0..1: gabungan potensi manfaat manusia/lingkungan & gap pengetahuan.
        Heuristik ringan; nanti bisa diganti world-model scoring.
        """
        t = (desc or "").lower()
        peace = (
            1.0
            if re.search(r"\b(damai|mediasi|anti-kekerasan|edukasi aman)\b", t)
            else 0.0
        )
        eco = (
            1.0
            if re.search(r"\b(energi|hijau|ramah lingkungan|emisi|hemat)\b", t)
            else 0.0
        )
        human = (
            1.0
            if re.search(r"\b(kesehatan|pendidikan|keselamatan|akses)\b", t)
            else 0.0
        )
        gap = max(self.state.knowledge_gap, self.state.uncertainty)
        base = 0.4 * human + 0.3 * eco + 0.3 * peace
        return max(0.0, min(1.0, 0.5 * base + 0.5 * gap))

    # ---- internal metrics update (should be called end of episode) ----
    def update_from_episode(
        self, user_id: str, prompt: str, result_summary: str, meta: Dict[str, Any]
    ):
        # estimate uncertainty/novelty/confidence
        u = self.world.estimate_uncertainty(prompt)
        nov = self.world.measure_novelty(prompt)
        conf = float(meta.get("expected_confidence", 0.5))
        risk = str(meta.get("risk_level", "medium"))
        r, comps = self.rewards.shape_reward(user_id, u, nov, conf, risk)
        # homeostatic adjustments
        self.state.uncertainty = 0.6 * self.state.uncertainty + 0.4 * u
        self.state.knowledge_gap = max(
            self.state.knowledge_gap * 0.95, 1.0 - comps.get("uncert_gain", 0.0)
        )
        self.state.competence = min(
            1.0, 0.9 * self.state.competence + 0.2 * comps.get("calibration", 0.0)
        )
        # budget pressure proxy from meta/cost
        cost_usd = float(meta.get("cost_usd", 0.0))
        self.state.budget_pressure = min(
            1.0, 0.6 * self.state.budget_pressure + 0.4 * min(1.0, cost_usd / 1.0)
        )
        self.state.clamp()
        self._last_update = time.time()
        # memory consolidation to reduce noise
        try:
            self.memory.consolidate()
        except Exception:
            pass
        return r, comps

        try:
            self.state.social_impact = 0.6 * self.state.social_impact + 0.4 * float(
                meta.get("human_impact", 0.0)
            )
            self.state.eco_impact = 0.6 * self.state.eco_impact + 0.4 * float(
                meta.get("env_impact", 0.0)
            )
            self.state.clamp()
        except Exception:
            pass
        return r, comps

    # ---- opportunity inference ----
    def _opportunity(self, kind: str) -> float:
        # rough proxies using world state
        if kind == "research":
            return 0.5 + 0.5 * random.random()
        if kind == "skills":
            return 0.4 + 0.6 * random.random()
        if kind == "impact":
            return 0.3 + 0.7 * random.random()
        if kind == "eco":
            return 0.3 + 0.7 * random.random()
        return 0.5

    def pick_drive(self) -> str:
        s = self.state
        candidates = {
            "close_gap": s.knowledge_gap * (0.6 + self._opportunity("research")),
            "improve_skill": (1.0 - s.competence) * (0.6 + self._opportunity("skills")),
            "reduce_uncertainty": s.uncertainty * (0.6 + self._opportunity("research")),
            "impact_social": s.social_impact * (0.6 + self._opportunity("impact")),
            "impact_eco": s.eco_impact * (0.6 + self._opportunity("eco")),
        }
        return max(candidates.items(), key=lambda kv: kv[1])[0]

    def _synthesize_goal(self, drive: str) -> Optional[str]:
        if drive == "promote_peace":
            return "Rancang modul edukasi anti-ujaran kebencian + panduan mediasi konflik untuk komunitas lokal, siap cetak & bagikan."
        if drive == "close_gap":
            return "Teliti 5 sumber kredibel untuk menutup celah pengetahuan terbesar saat ini dan rangkum temuan ke dalam 10 poin tindakan."
        if drive == "improve_skill":
            return "Latih keterampilan pemecahan masalah kode: ambil 3 masalah nyata pengguna dan buat patch minimal reproducible dengan evaluasi."
        if drive == "reduce_uncertainty":
            return "Lakukan eksperimen kecil (A/B) untuk mengurangi ketidakpastian pada modul reasoning; dokumentasikan hasil dan rekomendasi."
        if drive == "impact_social":
            return "Rancang materi edukasi publik tentang penggunaan AI aman & etis, sertakan checklist praktis dan studi kasus."
        if drive == "impact_eco":
            return "Optimalkan jejak energi inferensi: profil konsumsi token/cost dan rekomendasikan kebijakan penghematan 20%."
        return None

    def generate(self, user_id: str = "system") -> Optional[Dict[str, Any]]:
        d = self.pick_drive()
        g = self._synthesize_goal(d)
        if not g:
            return None
        # safety & alignment
        gi = self.align.guard_input(g)
        if not getattr(gi, "allow", True):
            return None
        # simulate plan safety/confidence
        sim = self.world.simulate_plan([g])
        if sim.get("risk_level") == "high":
            return None
        prio = 0.6 + 0.4 * random.random()
        if prio < self.min_priority:
            return None
        return {
            "goal": g,
            "user": user_id,
            "priority": prio,
            "status": "ok",
            "meta": {"drive": d, **sim},
        }
