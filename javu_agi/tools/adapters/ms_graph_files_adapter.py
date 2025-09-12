from __future__ import annotations
import os, requests
from typing import Dict, Any

API = "https://graph.microsoft.com/v1.0"


def _hdr():
    t = os.getenv("MS_ACCESS_TOKEN")
    if not t:
        return None
    return {"Authorization": f"Bearer {t}"}


class MSGraphFilesAdapter:
    def list_root(self) -> Dict[str, Any]:
        h = _hdr()
        if not h:
            return {"status": "error", "reason": "no_token"}
        r = requests.get(f"{API}/me/drive/root/children", headers=h, timeout=12)
        return {"status": "ok" if r.ok else "error", "data": r.json()}

    def download(self, item_id: str) -> Dict[str, Any]:
        h = _hdr()
        if not h:
            return {"status": "error", "reason": "no_token"}
        r = requests.get(
            f"{API}/me/drive/items/{item_id}/content", headers=h, timeout=30
        )
        return {
            "status": "ok" if r.ok else "error",
            "content": r.content,
            "code": r.status_code,
        }

    def upload_text(self, path: str, text: str) -> Dict[str, Any]:
        h = _hdr()
        if not h:
            return {"status": "error", "reason": "no_token"}
        # small file upload
        r = requests.put(
            f"{API}/me/drive/root:/{path}:/content",
            headers=h,
            data=text.encode("utf-8"),
            timeout=30,
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

    def list_site_drive(self, site_id: str, top: int = 50) -> Dict[str, Any]:
        h = _hdr()
        if not h:
            return {"status": "error", "reason": "no_token"}
        try:
            r = requests.get(
                f"{API}/sites/{site_id}/drive/root/children",
                params={"$top": top},
                headers=h,
                timeout=12,
            )
            return {"status": "ok" if r.ok else "error", "data": r.json()}
        except Exception as e:
            return {"status": "error", "reason": str(e)}
