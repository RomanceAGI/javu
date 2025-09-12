"""
Simple circuit-breaker to suspend autonomous actions when error/risk rates spike.
Tracks counts in-memory and persists snapshot to artifacts for visibility.

Trip conditions are conservative and configurable via ENV.
"""
from __future__ import annotations
import time
import os
from typing import Dict
from javu_agi.utils.logging_config import get_logger
from javu_agi.utils.atomic_write import write_atomic
import json

logger = get_logger("javu_agi.safety.circuit_breaker")

SNAPSHOT = os.path.join(os.getenv("ARTIFACTS_DIR", "artifacts"), "circuit_breaker.json")
os.makedirs(os.path.dirname(SNAPSHOT), exist_ok=True)

class CircuitBreaker:
    def __init__(self, window_s: int = 60, threshold: int = 10):
        self.window_s = int(os.getenv("CB_WINDOW_S", str(window_s)))
        self.threshold = int(os.getenv("CB_THRESHOLD", str(threshold)))
        self.events = []  # list of timestamps of negative events

    def record_failure(self):
        ts = time.time()
        self.events.append(ts)
        # prune
        self.events = [e for e in self.events if e >= ts - self.window_s]
        self._maybe_snapshot()

    def should_trip(self) -> bool:
        ts = time.time()
        self.events = [e for e in self.events if e >= ts - self.window_s]
        trip = len(self.events) >= self.threshold
        if trip:
            logger.warning("Circuit breaker tripped: %s events in last %s seconds", len(self.events), self.window_s)
        return trip

    def _maybe_snapshot(self):
        try:
            write_atomic(SNAPSHOT, json.dumps({"ts": int(time.time()), "events": len(self.events)}, indent=2))
        except Exception:
            logger.exception("Failed write CB snapshot")

# singleton instance
CB = CircuitBreaker()