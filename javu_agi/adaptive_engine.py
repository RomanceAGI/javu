from javu_agi.memory.memory import recall_from_memory, save_to_memory
from javu_agi.utils.logger import log_user


def adapt_behavior(user_id, failure_tag="interaksi gagal"):
    context = recall_from_memory(user_id, failure_tag)
    if context and "tidak merespon" in context:
        log_user(user_id, "[ADAPTASI] Deteksi kegagalan → strategi diperbaiki.")
        save_to_memory(user_id, "[ADAPTASI] Strategi diperbaiki berdasarkan kegagalan.")
        return "Saya akan coba strategi baru di respon berikutnya"
    return None
