from __future__ import annotations
import os, json, hashlib, time
from typing import Any, Dict


class AuditLog:
    def __init__(self, path: str) -> None:
        self.path = path
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        self._prev = self._tail_hash()

    def _tail_hash(self) -> str:
        try:
            with open(self.path, "rb") as f:
                last = f.readlines()[-1].decode("utf-8").strip()
            return json.loads(last).get("hash", "0" * 40)
        except Exception:
            return "0" * 40

    def write(self, record: Dict[str, Any]) -> Dict[str, Any]:
        payload = json.dumps(record, ensure_ascii=False, separators=(",", ":"))
        h = hashlib.sha1((self._prev + "|" + payload).encode()).hexdigest()
        out = {"prev": self._prev, "hash": h, "ts": int(time.time()), "record": record}
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(out, ensure_ascii=False) + "\n")
        self._prev = h
        return out
