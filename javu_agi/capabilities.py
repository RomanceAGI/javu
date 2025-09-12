from __future__ import annotations
import os
from typing import Dict, List

# default: aman. override via ENV: CAP_ALLOW="net,read,write,python,bash"
DEFAULT = {"net", "read", "write", "python", "bash"}

TOOL_CATEGORY: Dict[str, str] = {
    "curl": "net",
    "wget": "net",
    "http": "net",
    "cat": "read",
    "grep": "read",
    "echo": "write",
    "tee": "write",
    "python": "python",
    "bash": "bash",
    # tambahkan tool internal lo di sini...
}


def allowed_categories() -> set[str]:
    raw = os.getenv("CAP_ALLOW", "").strip()
    if not raw:
        return set(DEFAULT)
    return {t.strip() for t in raw.split(",") if t.strip()}


def filter_steps(steps: List[Dict], allow: set[str]) -> List[Dict]:
    out = []
    for s in steps or []:
        t = (s.get("tool") or "").lower()
        cat = TOOL_CATEGORY.get(t, "read")
        if cat in allow:
            out.append(s)
    return out
