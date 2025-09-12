from __future__ import annotations
import os, requests
from typing import Dict, Any


class TelegramAdapter:
    def __init__(self):
        self.token = os.getenv("TELEGRAM_BOT_TOKEN", "")

    def send(self, chat_id: str, text: str) -> Dict[str, Any]:
        if not self.token:
            return {"status": "error", "reason": "no_token"}
        r = requests.post(
            f"https://api.telegram.org/bot{self.token}/sendMessage",
            json={"chat_id": chat_id, "text": text},
            timeout=8,
        )
        return {"status": "ok" if r.ok else "error", "data": r.json()}

    def get_updates(self, offset: int = None, limit: int = 50) -> Dict[str, Any]:
        if not self.token:
            return {"status": "error", "reason": "no_token"}
        params = {"limit": limit}
        if offset is not None:
            params["offset"] = offset
        r = requests.get(
            f"https://api.telegram.org/bot{self.token}/getUpdates",
            params=params,
            timeout=8,
        )
        return {"status": "ok" if r.ok else "error", "data": r.json()}
