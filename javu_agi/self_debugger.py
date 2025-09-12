from javu_agi.memory.memory import recall_from_memory
from javu_agi.utils.logger import log_user


def self_debug(user_id, step, result):
    error_keywords = ["error", "gagal", "invalid", "tidak bisa"]
    if any(k in result.lower() for k in error_keywords):
        msg = f"[DEBUG] Step gagal → {step} → hasil: {result}"
        log_user(user_id, msg)
        return msg
    log_user(user_id, "[DEBUG] Semua berjalan lancar.")
    return "[DEBUG] Semua berjalan lancar."
