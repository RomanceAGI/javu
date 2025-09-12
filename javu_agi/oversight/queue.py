import threading, time, uuid
from collections import deque


class OversightQueue:
    def __init__(self):
        self.lock = threading.Lock()
        self.q = deque()
        self.pending = {}

    def submit(self, item: dict) -> str:
        rid = str(uuid.uuid4())
        with self.lock:
            item = {**item, "id": rid, "ts": int(time.time()), "status": "pending"}
            self.pending[rid] = item
            self.q.append(rid)
        return rid

    def list_pending(self) -> list[dict]:
        with self.lock:
            return [
                self.pending[r]
                for r in list(self.pending.values())
                if r["status"] == "pending"
            ]

    def approve(self, rid: str, note: str = "") -> bool:
        with self.lock:
            it = self.pending.get(rid)
            if not it:
                return False
            it["status"] = "approved"
            it["note"] = note
            return True

    def reject(self, rid: str, note: str = "") -> bool:
        with self.lock:
            it = self.pending.get(rid)
            if not it:
                return False
            it["status"] = "rejected"
            it["note"] = note
            return True

    def get(self, rid: str) -> dict | None:
        with self.lock:
            return self.pending.get(rid)
