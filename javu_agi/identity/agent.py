from __future__ import annotations
from typing import List, Dict, Any, Optional
import time


class IdentityAgent:
    """
    Self-model sederhana (pro):
    - profile & objectives
    - next_objective(): goal selection
    - learn_from(): self-improvement hooks
    - communicator (opsional) diisi dari luar
    """

    def __init__(self, name: str = "JAVU", role: str = "Digital General Intelligence"):
        self.name = name
        self.role = role
        self.objectives: List[str] = [
            "Perbaiki akurasi jawaban pada domain teknis.",
            "Kurangi ketidakpastian di topik baru.",
            "Tingkatkan efisiensi penggunaan tool.",
        ]
        self.history: List[Dict[str, Any]] = []
        self.communicator = None  # diisi dari luar jika ada multi-agent

    def next_objective(self) -> Optional[str]:
        # pilih objektif yang belum dikerjakan lama (round-robin sederhana)
        if not self.objectives:
            return None
        idx = int(time.time()) % len(self.objectives)
        return self.objectives[idx]

    def learn_from(self, output: str, context: Dict[str, Any] | None = None):
        """
        Hook pembelajaran diri (ringan):
        - log outcome & reward jika ada
        - adaptasi daftar objectives (contoh: masukkan objective baru bila reward rendah)
        """
        ctx = context or {}
        reward = float(ctx.get("reward", 0.0))
        self.history.append(
            {"t": int(time.time()), "out": output[:400], "reward": reward}
        )

        # adaptif very-light
        if (
            reward < 0.3
            and "kurangi ketidakpastian" not in " ".join(self.objectives).lower()
        ):
            self.objectives.append(
                "Kurangi ketidakpastian lewat retrieval + klarifikasi singkat."
            )

    # opsional: interface ke multi-agent communicator
    def send(self, to: str, msg: str):
        if self.communicator:
            self.communicator.send(self.name, to, msg)
