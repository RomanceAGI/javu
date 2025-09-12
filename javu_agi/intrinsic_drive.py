from javu_agi.memory.memory import recall_from_memory
from javu_agi.user_state import get_state
from javu_agi.utils.logger import log_user


def generate_intrinsic_goal(user_id):
    state = get_state(user_id)
    if state.get("status") == "idle":
        goal = "Pelajari topik baru yang belum diketahui"
    elif "komplain" in recall_from_memory(user_id, "masalah"):
        goal = "Cari penyebab utama masalah user sebelumnya"
    else:
        goal = "Tingkatkan kapasitas reasoning dan kemampuan menyelesaikan masalah"
    log_user(user_id, f"[INTRINSIC_GOAL] {goal}")
    return goal
