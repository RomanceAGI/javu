from __future__ import annotations
import os, base64, requests
from typing import Dict, Any

API = "https://gmail.googleapis.com/gmail/v1"


def _hdr():
    t = os.getenv("GMAIL_ACCESS_TOKEN")  # access token dari refresh-token flow
    if not t:
        return None
    return {"Authorization": f"Bearer {t}", "Accept": "application/json"}


def _b64raw(to: str, subject: str, body: str) -> str:
    raw = f"To: {to}\r\nSubject: {subject}\r\n\r\n{body}".encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("utf-8")


class GmailAdapter:
    def list_messages(self, q: str = "", max_n: int = 20) -> Dict[str, Any]:
        h = _hdr()
        if not h:
            return {"status": "error", "reason": "no_token"}
        r = requests.get(
            f"{API}/users/me/messages",
            params={"q": q, "maxResults": max_n},
            headers=h,
            timeout=10,
        )
        return {"status": "ok" if r.ok else "error", "data": r.json()}

    def get_message(self, msg_id: str) -> Dict[str, Any]:
        h = _hdr()
        if not h:
            return {"status": "error", "reason": "no_token"}
        r = requests.get(f"{API}/users/me/messages/{msg_id}", headers=h, timeout=10)
        return {"status": "ok" if r.ok else "error", "data": r.json()}

    def send(self, to: str, subject: str, body: str) -> Dict[str, Any]:
        h = _hdr()
        if not h:
            return {"status": "error", "reason": "no_token"}
        r = requests.post(
            f"{API}/users/me/messages/send",
            headers=h,
            json={"raw": _b64raw(to, subject, body)},
            timeout=12,
        )
        try:
            data = r.json()
        except Exception:
            data = {"text": r.text}
        return {
            "status": "ok" if r.ok else "error",
            "data": data,
            "code": r.status_code,
        }
