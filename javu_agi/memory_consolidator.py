from __future__ import annotations
import time
from typing import Dict, Any, List


def consolidate(ltm, distill, dedup, tag: str = "daily"):
    """
    Ambil event terbaru dari LTM, buat ringkasan, simpan ke distill (dedup by tag+date).
    """
    try:
        today = time.strftime("%Y-%m-%d")
        summ = ltm.summarize_recent(200)
        key = f"ltm/{tag}/{today}.json"
        rid = f"ltm:{tag}:{today}"

        if dedup and getattr(dedup, "has", None) and dedup.has(rid):
            return {"ok": True, "skipped": True}

        distill.write_json(key, {"date": today, "summary": summ})
        if dedup and getattr(dedup, "mark", None):
            dedup.mark(rid)
        return {"ok": True, "skipped": False, "path": key}
    except Exception as e:
        return {"ok": False, "error": str(e)}
