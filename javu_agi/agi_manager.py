from __future__ import annotations
import os
import threading
import time
from javu_agi.identity import load_identity
from javu_agi.autonomous_loop import run_autonomous_loop
from javu_agi.utils.logger import log_system

ACTIVE_USERS = ["user-001", "user-002", "user-003"]
ACTIVE_THREADS = {}

def start_instance(user_id):
    identity = load_identity(user_id)
    log_system(f"[START] AGI aktif untuk {user_id} ({identity.get('name')})")
    run_autonomous_loop(user_id)

def start_all_instances():
    threads = []
    for user_id in ACTIVE_USERS:
        t = threading.Thread(target=start_instance, args=(user_id,))
        t.start()
        threads.append(t)

    for t in threads:
        t.join()
    return threads

if __name__ == "__main__":
    log_system("🚀 Menyalakan semua instans AGI...")
    start_all_instances()
