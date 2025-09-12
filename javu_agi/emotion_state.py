from javu_agi.user_state import get_state, update_state
from javu_agi.utils.logger import log_user
from javu_agi.audit.audit_chain import AuditChain
import threading, os

EMOTIONS = ["curiosity", "fatigue", "focus", "excitement", "confusion", "satisfaction"]
_LOCKS = {}


def _lock(uid):
    if uid not in _LOCKS:
        _LOCKS[uid] = threading.Lock()
    return _LOCKS[uid]


def update_emotion(user_id, key, delta):
    if key not in EMOTIONS:
        EMOTIONS.append(key)
    with _lock(user_id):
        state = get_state(user_id)
        value = max(0, min(10, state.get(key, 5) + delta))
        update_state(user_id, key, value)
        log_user(user_id, f"[EMOTION] {key} updated to {value}")
        try:
            AuditChain(log_dir=os.getenv("AUDIT_CHAIN_DIR", "logs/audit_chain")).commit(
                "affect_update", {"user": user_id, "key": key, "val": value}
            )
        except Exception:
            pass
