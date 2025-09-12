from javu_agi.memory.memory import recall_from_memory
from javu_agi.utils.logger import log_user

def self_debug(user_id, step, result):
    """Simple debug logger: only treats textual results safely."""
    error_keywords = ["error", "gagal", "invalid", "tidak bisa"]
    try:
        res_text = str(result) if result is not None else ""
        low = res_text.lower()
    except Exception:
        res_text = "<non-textual result>"
        low = "<non-textual result>"
    if any(k in low for k in error_keywords):
        msg = f"[DEBUG] Step gagal → {step} → hasil: {res_text}"
        log_user(user_id, msg)
        return msg
    log_user(user_id, "[DEBUG] Semua berjalan lancar.")
    return "[DEBUG] Semua berjalan lancar."
    
