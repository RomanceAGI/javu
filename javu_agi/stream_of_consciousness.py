from javu_agi.memory.memory_manager import load_recent_memory
from javu_agi.utils.logger import log_user

user_streams = {}


def think_aloud(user_id: str):
    recent = load_recent_memory(user_id)
    thought = f"Saya mengingat: {recent}"

    if user_id not in user_streams:
        user_streams[user_id] = []

    user_streams[user_id].append(thought)
    user_streams[user_id] = user_streams[user_id][-25:]  # limit 25

    log_user(user_id, f"[STREAM] {thought}")
    return thought


def get_stream(user_id: str) -> list[str]:
    return user_streams.get(user_id, [])
