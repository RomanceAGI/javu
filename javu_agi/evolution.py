from javu_agi.user_state import get_state, log_action
from javu_agi.utils.logger import log_user


def evolve(user_id):
    state = get_state(user_id)
    last = state.get("last_action", "")
    if any(t in last for t in ["error", "stuck", "loop", "fail"]):
        log_action(user_id, "[EVOLUTION] Deteksi anomali → strategi diubah.")
        log_user(user_id, "[EVOLUTION] Strategi diperbarui karena anomali aksi.")
