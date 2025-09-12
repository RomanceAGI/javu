from __future__ import annotations
import os, requests
from typing import Dict, Any

API = "https://graph.microsoft.com/v1.0"


def _hdr():
    t = os.getenv("MS_ACCESS_TOKEN")
    if not t:
        return None
    return {"Authorization": f"Bearer {t}", "Accept": "application/json"}


class MSGraphMailAdapter:
    def list_messages(self, top: int = 20) -> Dict[str, Any]:
        h = _hdr()
        if not h:
            return {"status": "error", "reason": "no_token"}
        r = requests.get(
            f"{API}/me/messages", params={"$top": top}, headers=h, timeout=10
        )
        return {"status": "ok" if r.ok else "error", "data": r.json()}

    def send(self, to: str, subject: str, body: str) -> Dict[str, Any]:
        h = _hdr()
        if not h:
            return {"status": "error", "reason": "no_token"}
        payload = {
            "message": {
                "subject": subject,
                "body": {"contentType": "Text", "content": body},
                "toRecipients": [{"emailAddress": {"address": to}}],
            },
            "saveToSentItems": True,
        }
        r = requests.post(
            f"{API}/me/sendMail",
            headers={**h, "Content-Type": "application/json"},
            json=payload,
            timeout=12,
        )
        try:
            data = r.json()
        except Exception:
            data = {"text": r.text}
        return {
            "status": "ok" if r.status_code in (202, 200) else "error",
            "data": data,
            "code": r.status_code,
        }
