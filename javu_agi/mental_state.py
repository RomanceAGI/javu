from javu_agi.user_state import get_state, update_state
from javu_agi.utils.logger import log_user

MENTAL_VARIABLES = ["energy", "focus", "motivation"]


def update_mental_state(user_id, variable, delta):
    state = get_state(user_id)
    current = state.get(variable, 5)
    new_val = max(0, min(10, current + delta))
    update_state(user_id, variable, new_val)
    log_user(user_id, f"[MENTAL] {variable}: {current} → {new_val}")
    return new_val
