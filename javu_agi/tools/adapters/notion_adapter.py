from __future__ import annotations
import os, requests
from typing import Dict, Any

API = "https://api.notion.com/v1"
NOTION_VER = os.getenv("NOTION_VERSION", "2022-06-28")


def _hdr():
    tok = os.getenv("NOTION_TOKEN", "")
    if not tok:
        return None
    return {
        "Authorization": f"Bearer {tok}",
        "Notion-Version": NOTION_VER,
        "Content-Type": "application/json",
    }


class NotionAdapter:
    def search(self, query: str = "", page_size: int = 20) -> Dict[str, Any]:
        h = _hdr()
        if not h:
            return {"status": "error", "reason": "no_token"}
        try:
            r = requests.post(
                f"{API}/search",
                headers=h,
                json={"query": query, "page_size": page_size},
                timeout=10,
            )
            return {"status": "ok" if r.ok else "error", "data": r.json()}
        except Exception as e:
            return {"status": "error", "reason": str(e)}

    def create_page(
        self, parent_id: str, title: str, content: str = ""
    ) -> Dict[str, Any]:
        """
        parent_id bisa database_id (pakai {"database_id":...}) atau page_id (pakai {"page_id":...}).
        Di sini default ke page parent. Kalau mau database, ubah 'parent' sesuai kebutuhan.
        """
        h = _hdr()
        if not h:
            return {"status": "error", "reason": "no_token"}
        payload = {
            "parent": {"page_id": parent_id},
            "properties": {"title": [{"text": {"content": title}}]},
            "children": [
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{"type": "text", "text": {"content": content}}]
                    },
                }
            ],
        }
        try:
            r = requests.post(f"{API}/pages", headers=h, json=payload, timeout=12)
            return {
                "status": "ok" if r.ok else "error",
                "data": r.json(),
                "code": r.status_code,
            }
        except Exception as e:
            return {"status": "error", "reason": str(e)}
