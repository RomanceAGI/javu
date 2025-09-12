from __future__ import annotations
from typing import Optional

def _build_role_hint(role: Optional[str]) -> str:
    if not role:
        return ""
    r = str(role).strip()
    # normalize dangerous chars and whitespace
    r = " ".join(r.split())
    return f"[role={r}]"
