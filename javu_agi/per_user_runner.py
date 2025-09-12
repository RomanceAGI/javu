import threading
from javu_agi.autonomous_loop import run_autonomous_loop
from javu_agi.identity import load_identity

ACTIVE_USERS = ["user-001", "user-002", "user-003"]


def start_user_instance(user_id):
    try:
        identity = load_identity(user_id)
        print(f"🧠 JAVU.AGI AKTIF untuk {identity.get('name')} ({user_id})")
        run_autonomous_loop(user_id)
    except Exception as e:
        print(f"[ERROR] {user_id} → {e}")


def start_all_users():
    threads = []
    for user_id in ACTIVE_USERS:
        t = threading.Thread(target=start_user_instance, args=(user_id,))
        t.start()
        threads.append(t)

    for t in threads:
        t.join()


if __name__ == "__main__":
    print("🚀 Menyalakan semua instans AGI per user...")
    start_all_users()
