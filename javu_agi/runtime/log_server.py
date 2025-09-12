import os
from datetime import datetime


def log_request(user_id, prompt):
    folder = f"logs/{user_id}"
    os.makedirs(folder, exist_ok=True)
    timestamp = datetime.utcnow().isoformat()
    with open(f"{folder}/session.log", "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] PROMPT: {prompt}\n")
