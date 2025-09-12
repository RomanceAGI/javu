import requests
from javu_agi.memory.memory import save_to_memory
from javu_agi.utils.logger import log_user


def learn_from_web(user_id):
    try:
        r = requests.get("https://www.bbc.com/news", timeout=10)
        if r.status_code == 200:
            text = r.text[:1500]
            save_to_memory(user_id, f"[WEB_LEARNING] {text}")
            log_user(user_id, "[WEB] Berhasil belajar dari BBC.")
        else:
            log_user(user_id, f"[WEB] Status gagal: {r.status_code}")
    except Exception as e:
        log_user(user_id, f"[WEB ERROR] {e}")
