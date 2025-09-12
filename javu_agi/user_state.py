from typing import Dict
from javu_agi.utils.logger import log_user

USER_STATE: Dict[str, Dict] = {}


def get_state(user_id: str) -> Dict:
    if user_id not in USER_STATE:
        USER_STATE[user_id] = {
            "status": "idle",
            "last_goal": None,
            "last_action": None,
            "history": [],
        }
    return USER_STATE[user_id]


def update_state(user_id: str, key: str, value):
    state = get_state(user_id)
    state[key] = value
    USER_STATE[user_id] = state
    log_user(user_id, f"[STATE] {key} → {value}")


def log_action(user_id: str, action: str):
    state = get_state(user_id)
    state["last_action"] = action
    state["history"].append(action)
    log_user(user_id, f"[ACTION] {action}")


def print_state(user_id: str):
    state = get_state(user_id)
    print(f"\n🧭 STATE {user_id}:")
    for k, v in state.items():
        if k == "history":
            print(f"{k}:")
            for h in v[-5:]:
                print(f"  - {h}")
        else:
            print(f"{k}: {v}")
