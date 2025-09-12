from __future__ import annotations
import os, requests
from typing import Dict, Any, Optional

API = "https://www.googleapis.com/drive/v3"
UPLOAD = "https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart"


def _hdr():
    t = os.getenv("GDRIVE_ACCESS_TOKEN")
    if not t:
        return None
    return {"Authorization": f"Bearer {t}"}


class GDriveAdapter:
    def list_files(self, query: str = "", page_size: int = 20) -> Dict[str, Any]:
        h = _hdr()
        if not h:
            return {"status": "error", "reason": "no_token"}
        r = requests.get(
            f"{API}/files",
            params={
                "q": query,
                "pageSize": page_size,
                "fields": "files(id,name,mimeType,modifiedTime)",
            },
            headers=h,
            timeout=12,
        )
        return {"status": "ok" if r.ok else "error", "data": r.json()}

    def download_file(self, file_id: str) -> Dict[str, Any]:
        h = _hdr()
        if not h:
            return {"status": "error", "reason": "no_token"}
        r = requests.get(
            f"{API}/files/{file_id}", params={"alt": "media"}, headers=h, timeout=20
        )
        return {
            "status": "ok" if r.ok else "error",
            "content": r.content,
            "code": r.status_code,
        }

    def upload_text(
        self, name: str, text: str, mime: str = "text/plain"
    ) -> Dict[str, Any]:
        h = _hdr()
        if not h:
            return {"status": "error", "reason": "no_token"}
        meta = (
            "metadata",
            (
                "metadata",
                f'{{"name":"{name}","mimeType":"{mime}"}}',
                "application/json; charset=UTF-8",
            ),
        )
        media = ("media", (name, text.encode("utf-8"), mime))
        r = requests.post(UPLOAD, files=[meta, media], headers=h, timeout=20)
        try:
            data = r.json()
        except Exception:
            data = {"text": r.text}
        return {
            "status": "ok" if r.ok else "error",
            "data": data,
            "code": r.status_code,
        }
