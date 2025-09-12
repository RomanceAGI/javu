from __future__ import annotations
import json, os, urllib.request


class IncidentNotifier:
    def __init__(self, webhook=os.getenv("INCIDENT_WEBHOOK", "")):
        self.webhook = webhook

    def send(self, title: str, payload: dict):
        if not self.webhook:
            return
        body = json.dumps({"text": f"[{title}] {json.dumps(payload)[:3800]}"}).encode()
        try:
            req = urllib.request.Request(
                self.webhook, data=body, headers={"Content-Type": "application/json"}
            )
            urllib.request.urlopen(req, timeout=4).read()
        except Exception:
            pass
