from __future__ import annotations
import os, requests
from typing import Dict, Any

API = "https://people.googleapis.com/v1"


def _hdr():
    t = os.getenv("GCONTACTS_ACCESS_TOKEN")
    if not t:
        return None
    return {"Authorization": f"Bearer {t}", "Accept": "application/json"}


class GContactsAdapter:
    def list(self, page_size: int = 50) -> Dict[str, Any]:
        h = _hdr()
        if not h:
            return {"status": "error", "reason": "no_token"}
        r = requests.get(
            f"{API}/people/me/connections",
            params={
                "personFields": "names,emailAddresses,phoneNumbers",
                "pageSize": page_size,
            },
            headers=h,
            timeout=10,
        )
        return {"status": "ok" if r.ok else "error", "data": r.json()}
