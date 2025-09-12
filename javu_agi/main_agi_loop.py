from __future__ import annotations
import os
import time
import threading
from typing import Optional

from javu_agi.runtime.state_persistence import load_state, save_state
from javu_agi.core_loop import run_core_loop
from javu_agi.memory.memory_manager import MemoryManager
from javu_agi.identity.agent import IdentityAgent
from javu_agi.obs.metrics import M
from javu_agi.identity.objectives import ObjectiveManager

# ===== CONFIG AMAN / MAXIMAL =====
DATA_DIR = os.getenv("DATA_DIR", "/data")
RUNTIME_DIR = os.getenv("RUNTIME_DIR", os.path.join(DATA_DIR, "runtime"))
STATE_FILES = {
    "identity": os.path.join(RUNTIME_DIR, "identity.pkl"),
    "memory": os.path.join(RUNTIME_DIR, "memory.pkl"),
}

STOP_FILE = os.path.join(RUNTIME_DIR, ".stop")
TICK_INTERVAL = float(os.getenv("AGI_TICK_INTERVAL", "0.5"))  # detik

# Pastikan folder persistence ada
os.makedirs(RUNTIME_DIR, exist_ok=True)


class AGILoop:
    """
    Loop utama AGI — autonomous & continuous.
    Aman untuk crash/restart karena semua state ada di volume /data/runtime.
    """

    def __init__(self):
        self.identity: IdentityAgent = (
            load_state(STATE_FILES["identity"]) or IdentityAgent()
        )
        self.memory: MemoryManager = (
            load_state(STATE_FILES["memory"]) or MemoryManager()
        )
        self.running: bool = True
        self.lock = threading.Lock()
        self.objectives = ObjectiveManager()

    def tick(self):
        """
        Satu langkah AGI. Bisa autonomous (tanpa input) atau reactive (dengan input).
        """
        try:
            # Ambil prompt dari identity atau memori (self-tasking)
            prompt = self.identity.next_objective() or self.memory.get_pending_task()

            if not prompt:
                prompt = "Evaluasi keadaan dan cari peluang baru."

            # Jalankan core loop
            try:
                result = run_core_loop(user_id="__AGI__", full_input=prompt)
            except Exception as e:
                result = {"response": f"[LOOP ERROR] {e}", "meta": {"error": True}}

            # Store hasil
            self.memory.store_autonomous(result["response"], meta=result["meta"])

            # Metrics
            M.loop_ticks.inc()
            if "reward" in result["meta"]:
                M.reward.observe(result["meta"]["reward"])

                # Adaptive learning is disabled by default.  Set ENABLE_SELF_LEARN=1 to enable.
                if os.getenv("ENABLE_SELF_LEARN", "0") == "1":
                    self.identity.learn_from(result["response"], context=result["meta"])

            # backoff ringan saat error
            sl = TICK_INTERVAL * (2.0 if result.get("meta", {}).get("error") else 1.0)
            time.sleep(sl)

        except Exception as e:
            print(f"[AGILoop] ERROR tick: {e}")

    def save_state(self):
        """
        Simpan semua state penting ke storage persistence.
        """
        try:
            save_state(STATE_FILES["identity"], self.identity)
            save_state(STATE_FILES["memory"], self.memory)
        except Exception as e:
            print(f"[AGILoop] ERROR save_state: {e}")

    def should_stop(self) -> bool:
        """
        Cek file STOP untuk graceful shutdown.
        """
        return os.path.exists(STOP_FILE)

    def run_forever(self):
        print("🚀 AGI Loop started. Tick every", TICK_INTERVAL, "seconds.")
        while self.running:
            if self.should_stop():
                print("🛑 STOP signal detected. Exiting...")
                break
            self.tick()
            self.save_state()
            time.sleep(TICK_INTERVAL)

        # Simpan terakhir saat berhenti
        self.save_state()
        print("💾 Final state saved. Loop ended.")


if __name__ == "__main__":
    loop = AGILoop()
    loop.run_forever()
