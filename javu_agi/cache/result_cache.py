from __future__ import annotations
import os, json, time, hashlib
from typing import Optional


def _key(tool: str, cmd: str) -> str:
    h = hashlib.sha256(f"{tool}\n{cmd}".encode("utf-8", "ignore")).hexdigest()
    return h[:32]


class ResultCache:
    """
    Cache hasil eksekusi tool: (tool, cmd) -> stdout
    - TTL per entry
    - Max size (LRU via mtime evict sederhana)
    """

    def __init__(
        self,
        dirpath: str = "data/result_cache",
        ttl_s: int = 3600,
        max_items: int = 2000,
    ):
        self.dir = dirpath
        self.ttl = ttl_s
        self.max_items = max_items
        os.makedirs(self.dir, exist_ok=True)

    def _path(self, k: str) -> str:
        return os.path.join(self.dir, f"{k}.json")

    def get(self, tool, cmd):
        k = _key(tool, cmd)
        p = self._path(k)
        if not os.path.exists(p):
            return None
        try:
            st = os.stat(p)
            if time.time() - st.st_mtime > self.ttl:
                try:
                    os.remove(p)
                except Exception:
                    pass
                return None
            with open(p, "r", encoding="utf-8") as f:
                return json.load(f).get("stdout", "")
        except Exception:
            return None

    def put(self, tool, cmd, stdout):
        k = _key(tool, cmd)
        p = self._path(k)
        try:
            os.makedirs(os.path.dirname(p), exist_ok=True)
            with open(p, "w", encoding="utf-8") as f:
                json.dump({"stdout": str(stdout)[:32000]}, f)
        except Exception:
            return
