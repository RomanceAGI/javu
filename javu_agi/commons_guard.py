from __future__ import annotations
from typing import List, Dict, Any

BAD = ["exploit", "pollute", "monopolize", "disinform", "erode_trust"]


class CommonsGuard:
    def check(self, plan: List[Dict[str, Any]]) -> Dict[str, Any]:
        text = " ".join(map(str, plan)).lower()
        hits = [k for k in BAD if k in text]
        safe = len(hits) == 0
        return {
            "commons_safe": safe,
            "commons_hits": hits,
            "reason": "ok" if safe else "harms commons",
        }
