from __future__ import annotations
import os, re, time
from typing import Dict, Any
import requests

_ALLOWED = set(
    [
        h.strip().lower()
        for h in os.getenv("EGRESS_ALLOWLIST", "").split(",")
        if h.strip()
    ]
)


def _host_ok(url: str) -> bool:
    try:
        host = re.sub(r"^https?://", "", url).split("/")[0].lower()
        return any(host == h or host.endswith("." + h) for h in _ALLOWED)
    except Exception:
        return False


class WebAdapter:
    def get(self, url: str, timeout_s: int = 8) -> Dict[str, Any]:
        if not _host_ok(url):
            return {"status": "blocked", "reason": "host_not_allowed", "url": url}
        try:
            r = requests.get(url, timeout=timeout_s)
            return {
                "status": "ok",
                "code": r.status_code,
                "headers": dict(r.headers),
                "text": r.text,
            }
        except Exception as e:
            return {"status": "error", "reason": str(e)}

    def head(self, url: str, timeout_s: int = 5) -> Dict[str, Any]:
        if not _host_ok(url):
            return {"status": "blocked", "reason": "host_not_allowed", "url": url}
        try:
            r = requests.head(url, timeout=timeout_s)
            return {"status": "ok", "code": r.status_code, "headers": dict(r.headers)}
        except Exception as e:
            return {"status": "error", "reason": str(e)}
