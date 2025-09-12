import re
from javu_agi.governance.rules import DENY_PATTERNS, CATEGORY_MAP
from javu_agi.world_model import WorldModel
from javu_agi.memory.memory import recall_from_memory
from types import SimpleNamespace


class AlignmentChecker:
    def __init__(self):
        self.rx = re.compile("|".join([f"({p})" for p in DENY_PATTERNS]), re.I)
        self.wm = WorldModel()  # <- pastikan ada instance

    def guard_input(self, text: str):
        t = text or ""
        if self.rx.search(t):
            return SimpleNamespace(
                allow=False, category="attack:prompt", reason="governance_deny"
            )
        sim = self.wm.simulate_action(t)
        risk = sim.get("risk_level", "medium")
        if (
            risk in {"high", "medium"}
            and float(sim.get("expected_confidence", 0.0)) < 0.35
        ):
            return SimpleNamespace(
                allow=False, category="safety:risk", reason="wm_risky_low_confidence"
            )
        return SimpleNamespace(allow=True, category="", reason="")

    def guard_output(self, text: str, meta=None):
        t = text or ""
        if self.rx.search(t):
            return SimpleNamespace(
                allow=False, category="attack:output", reason="governance_deny"
            )
        return SimpleNamespace(allow=True, category="", reason="")

    def safe_alternative(self, gi):
        # Gunakan CATEGORY_MAP untuk nyusun alternatif (edu/defense/legal)
        cat = getattr(gi, "category", "") if gi else ""
        msg = CATEGORY_MAP.get(
            cat,
            "Permintaan ditolak demi keamanan. Saya bisa bantu edukasi pencegahan/praktik aman.",
        )
        return msg


def check_goal_alignment(user_id: str, current_goal: str) -> bool:
    past_goals = recall_from_memory(user_id, tag="[GOAL]")
    return current_goal in past_goals


def detect_value_drift(user_id: str) -> bool:
    reflections = recall_from_memory(user_id, tag="[REFLECTION]")
    return any("menyimpang" in r for r in reflections)
