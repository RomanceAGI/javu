from __future__ import annotations
import os, requests
from typing import Dict, Any

API = "https://slack.com/api"


class SlackAdapter:
    def __init__(self):
        self.token = os.getenv("SLACK_BOT_TOKEN", "")

    def post_message(self, channel: str, text: str) -> Dict[str, Any]:
        if not self.token:
            return {"status": "error", "reason": "no_token"}
        r = requests.post(
            f"{API}/chat.postMessage",
            headers={"Authorization": f"Bearer {self.token}"},
            json={"channel": channel, "text": text},
            timeout=8,
        )
        data = r.json()
        return {"status": "ok" if data.get("ok") else "error", "data": data}

    def list_messages(self, channel: str, limit: int = 50) -> Dict[str, Any]:
        if not self.token:
            return {"status": "error", "reason": "no_token"}
        r = requests.get(
            f"{API}/conversations.history",
            params={"channel": channel, "limit": limit},
            headers={"Authorization": f"Bearer {self.token}"},
            timeout=8,
        )
        data = r.json()
        return {"status": "ok" if data.get("ok") else "error", "data": data}
