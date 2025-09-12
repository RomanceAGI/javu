from __future__ import annotations
import os, requests
from typing import Dict, Any

API = "https://www.googleapis.com/calendar/v3"


def _hdr():
    t = os.getenv("GCAL_ACCESS_TOKEN")
    if not t:
        return None
    return {"Authorization": f"Bearer {t}", "Accept": "application/json"}


class GCalAdapter:
    def list_events(
        self, calendar_id: str = "primary", q: str = "", max_n: int = 20
    ) -> Dict[str, Any]:
        h = _hdr()
        if not h:
            return {"status": "error", "reason": "no_token"}
        r = requests.get(
            f"{API}/calendars/{calendar_id}/events",
            params={
                "q": q,
                "maxResults": max_n,
                "singleEvents": True,
                "orderBy": "startTime",
            },
            headers=h,
            timeout=10,
        )
        return {"status": "ok" if r.ok else "error", "data": r.json()}

    def create_event(
        self,
        calendar_id: str,
        title: str,
        start_iso: str,
        end_iso: str,
        description: str = "",
    ) -> Dict[str, Any]:
        h = _hdr()
        if not h:
            return {"status": "error", "reason": "no_token"}
        payload = {
            "summary": title,
            "description": description,
            "start": {"dateTime": start_iso},
            "end": {"dateTime": end_iso},
        }
        r = requests.post(
            f"{API}/calendars/{calendar_id}/events", headers=h, json=payload, timeout=12
        )
        return {
            "status": "ok" if r.ok else "error",
            "data": r.json(),
            "code": r.status_code,
        }
