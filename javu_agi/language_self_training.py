from javu_agi.memory.memory import save_to_memory
from javu_agi.utils.logger import log_user


def reinforce_learning(user_id, step, result):
    pattern = f"[RL] Langkah '{step}' → hasil '{result}' dipelajari ulang."
    save_to_memory(user_id, pattern)
    log_user(user_id, pattern)
