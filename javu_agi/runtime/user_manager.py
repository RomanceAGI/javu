import json, os

DATA_DIR = os.getenv("DATA_DIR", "/data")
os.makedirs(DATA_DIR, exist_ok=True)
USER_DB = os.path.join(DATA_DIR, "user_db.json")


def load_users():
    if os.path.exists(USER_DB):
        with open(USER_DB, "r", encoding="utf-8") as f:
            return json.load(f)
    return ["admin"]


def validate_user(user_id):
    return user_id in load_users()
