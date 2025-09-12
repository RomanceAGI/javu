from __future__ import annotations
import os, time
from typing import Any, Dict


class ResilienceGuard:
    def __init__(self) -> None:
        self.max_qps = float(os.getenv("RES_MAX_QPS", "3"))
        self.window = float(os.getenv("RES_WINDOW_S", "10"))
        self._t = []
        self.tool_allow = (
            set((os.getenv("RES_TOOL_ALLOW") or "").split(","))
            if os.getenv("RES_TOOL_ALLOW")
            else None
        )

    def allow_request(self) -> bool:
        now = time.time()
        self._t = [t for t in self._t if now - t <= self.window]
        if len(self._t) >= self.max_qps * self.window:
            return False
        self._t.append(now)
        return True

    def allow_tool(self, name: str) -> bool:
        if self.tool_allow is None:
            return True
        return name in self.tool_allow
