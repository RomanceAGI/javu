from __future__ import annotations
import time, threading
from collections import defaultdict, deque
from typing import Tuple, Dict, Any


class UserLimitManager:
    def __init__(self, quota_guard=None, default_rpm: int = 90, window_s: int = 60):
        self.quota = quota_guard
        self.default_rpm = int(default_rpm)
        self.window_s = int(window_s)
        self._hist = defaultdict(deque)
        self._lock = threading.Lock()

    def allow_request(self, user_id: str) -> Tuple[bool, Dict[str, Any]]:
        now = time.time()
        with self._lock:
            dq = self._hist[user_id]
            while dq and now - dq[0] > self.window_s:
                dq.popleft()
            allow = len(dq) < self.default_rpm
            if allow:
                dq.append(now)
            meta = {"rpm_cap": self.default_rpm, "in_window": len(dq)}
        if self.quota:
            try:
                left = float(getattr(self.quota, "left_usd")(user_id))
                meta["usd_left"] = left
            except Exception:
                pass
        return allow, meta
