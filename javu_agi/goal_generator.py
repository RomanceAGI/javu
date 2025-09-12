import os
import random
import datetime
from javu_agi.safety_values import violates_core_values, explain_violation
from javu_agi.drive_system import DriveSystem
from javu_agi.world_model import WorldModel
from javu_agi.reward_system import RewardSystem
from javu_agi.memory.memory_manager import MemoryManager
from javu_agi.alignment_checker import AlignmentChecker

DEFAULT_GOALS = [
    "Pelajari 10 paper terbaru tentang AI alignment",
    "Susun rencana penelitian untuk meningkatkan efisiensi energi",
    "Analisis kebijakan publik X dan buat ringkasan objektif",
    "Optimalkan modul reasoning internal agar lebih hemat token",
    "Buat rencana proyek open-source untuk edukasi masyarakat",
    "Rancang proposal transparansi untuk pemerintahan anti-korupsi",
]

_DRV: DriveSystem | None = None


def _drv():
    global _DRV
    if _DRV is None:
        _DRV = DriveSystem(
            WorldModel(), RewardSystem(), MemoryManager(), AlignmentChecker()
        )

    return _DRV


def generate_goal(user_id: str = "system") -> dict:

    if os.getenv("ADVANCED_DRIVE", "1") == "1":
        g = _drv().generate(user_id)
        if g:
            return g

    raw_goal = random.choice(DEFAULT_GOALS)

    if violates_core_values(raw_goal):
        return {
            "goal": None,
            "status": "blocked",
            "reason": explain_violation(raw_goal),
            "ts": datetime.datetime.utcnow().isoformat(),
        }

    return {
        "goal": raw_goal,
        "user": user_id,
        "priority": random.uniform(0.3, 0.9),  # prioritas relatif
        "status": "ok",
        "ts": datetime.datetime.utcnow().isoformat(),
    }


def batch_generate(n: int = 3) -> list:
    """Generate beberapa goal sekaligus."""
    return [generate_goal() for _ in range(n)]
