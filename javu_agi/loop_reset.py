import os
import shutil
from javu_agi.utils.logger import log


def reset_agent_state(backup_dir: str = "backups/", memory_dir: str = "memory/"):
    try:
        log("[LOOP RESET] Resetting AGI state from backup...")

        if not os.path.exists(backup_dir):
            log("[LOOP RESET] No backup found.")
            return False

        if os.path.exists(memory_dir):
            shutil.rmtree(memory_dir)
            log(f"[LOOP RESET] Removed current memory at {memory_dir}")

        shutil.copytree(backup_dir, memory_dir)
        log(f"[LOOP RESET] Restored memory from {backup_dir} to {memory_dir}")
        return True

    except Exception as e:
        log(f"[LOOP RESET ERROR] {e}")
        return False
