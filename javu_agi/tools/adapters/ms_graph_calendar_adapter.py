from __future__ import annotations
import os, requests
from typing import Dict, Any

API = "https://graph.microsoft.com/v1.0"


def _hdr():
    t = os.getenv("MS_ACCESS_TOKEN")
    if not t:
        return None
    return {"Authorization": f"Bearer {t}", "Accept": "application/json"}


class MSGraphCalendarAdapter:
    def list_events(self, top: int = 20) -> Dict[str, Any]:
        h = _hdr()
        if not h:
            return {"status": "error", "reason": "no_token"}
        r = requests.get(
            f"{API}/me/events",
            params={"$top": top, "$orderby": "start/dateTime"},
            headers=h,
            timeout=10,
        )
        return {"status": "ok" if r.ok else "error", "data": r.json()}

    def create_event(
        self, title: str, start_iso: str, end_iso: str, description: str = ""
    ) -> Dict[str, Any]:
        h = _hdr()
        if not h:
            return {"status": "error", "reason": "no_token"}
        payload = {
            "subject": title,
            "body": {"contentType": "Text", "content": description},
            "start": {"dateTime": start_iso, "timeZone": "UTC"},
            "end": {"dateTime": end_iso, "timeZone": "UTC"},
        }
        r = requests.post(
            f"{API}/me/events",
            headers={**h, "Content-Type": "application/json"},
            json=payload,
            timeout=12,
        )
        return {
            "status": "ok" if r.ok else "error",
            "data": r.json(),
            "code": r.status_code,
        }
