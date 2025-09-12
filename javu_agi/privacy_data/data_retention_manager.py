from __future__ import annotations
import os, time, pathlib, shutil
from typing import List


class DataRetentionManager:
    def __init__(self, roots: List[str], ttl_days: int = 14):
        self.roots = [p for p in roots if p]
        self.ttl = ttl_days * 86400

    def purge(self):
        now = time.time()
        for root in self.roots:
            pathlib.Path(root).mkdir(parents=True, exist_ok=True)
            for dirpath, _, files in os.walk(root):
                for fn in files:
                    fp = os.path.join(dirpath, fn)
                    try:
                        if now - os.path.getmtime(fp) > self.ttl:
                            os.remove(fp)
                    except Exception:
                        pass
