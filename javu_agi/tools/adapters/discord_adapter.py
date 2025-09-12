from __future__ import annotations
import os, requests
from typing import Dict, Any

API = "https://discord.com/api/v10"


class DiscordAdapter:
    def __init__(self):
        self.bot = os.getenv("DISCORD_BOT_TOKEN", "")

    def post(self, channel_id: str, content: str) -> Dict[str, Any]:
        if not self.bot:
            return {"status": "error", "reason": "no_token"}
        r = requests.post(
            f"{API}/channels/{channel_id}/messages",
            headers={"Authorization": f"Bot {self.bot}"},
            json={"content": content},
            timeout=8,
        )
        try:
            data = r.json()
        except Exception:
            data = {"text": r.text}
        return {"status": "ok" if r.ok else "error", "data": data}

    def fetch(self, channel_id: str, limit: int = 20) -> Dict[str, Any]:
        if not self.bot:
            return {"status": "error", "reason": "no_token"}
        r = requests.get(
            f"{API}/channels/{channel_id}/messages",
            params={"limit": limit},
            headers={"Authorization": f"Bot {self.bot}"},
            timeout=8,
        )
        return {"status": "ok" if r.ok else "error", "data": r.json()}
