from __future__ import annotations
import os, time, json
from pathlib import Path


def evict_old_files(dirpath: str, ttl_s: int, pattern: str = "*.json"):
    d = Path(dirpath)
    if not d.exists():
        return 0
    now = time.time()
    n = 0
    for p in d.glob(pattern):
        try:
            if now - p.stat().st_mtime > ttl_s:
                p.unlink()
                n += 1
        except Exception:
            pass
    return n
