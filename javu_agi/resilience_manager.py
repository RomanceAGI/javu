from __future__ import annotations
import os, time, shutil, threading
from typing import Dict, Any, Optional

try:
    import psutil  # optional
except Exception:
    psutil = None


class CircuitBreaker:
    def __init__(self, fail_threshold: int = 5, cool_down_s: int = 30):
        self.fail_threshold = fail_threshold
        self.cool_down_s = cool_down_s
        self.fail_count = 0
        self.open_until = 0.0
        self._lock = threading.Lock()

    def fail(self):
        with self._lock:
            self.fail_count += 1
            if self.fail_count >= self.fail_threshold:
                self.open_until = time.time() + self.cool_down_s

    def ok(self):
        with self._lock:
            self.fail_count = max(0, self.fail_count - 1)

    def allow(self) -> bool:
        with self._lock:
            if time.time() < self.open_until:
                return False
            return True


class ResilienceManager:
    """
    Monitor resource, shed load, chaos toggle (for tests), circuit-breaker.
    """

    def __init__(
        self,
        cpu_high: float = 0.92,
        ram_high: float = 0.92,
        disk_min_bytes: int = 512 * 1024 * 1024,  # 512MB
        chaos_prob: float = 0.0,
    ):
        self.cpu_high = cpu_high
        self.ram_high = ram_high
        self.disk_min_bytes = disk_min_bytes
        self.chaos_prob = chaos_prob
        self.cb_exec = CircuitBreaker()
        self.cb_llm = CircuitBreaker()
        self.last_metrics: Dict[str, Any] = {}

    def _cpu_usage(self) -> float:
        if psutil:
            try:
                return psutil.cpu_percent(interval=0.05) / 100.0
            except Exception:
                pass
        # fallback
        try:
            la1, _, _ = os.getloadavg()
            return min(1.0, la1 / max(1, os.cpu_count() or 1))
        except Exception:
            return 0.0

    def _ram_usage(self) -> float:
        if psutil:
            try:
                return (psutil.virtual_memory().percent) / 100.0
            except Exception:
                pass
        return 0.0

    def _disk_free(self, path: str = ".") -> int:
        try:
            st = shutil.disk_usage(path)
            return st.free
        except Exception:
            return 10**12  # assume plenty

    def snapshot(self) -> Dict[str, Any]:
        m = {
            "ts": time.time(),
            "cpu": self._cpu_usage(),
            "ram": self._ram_usage(),
            "disk_free": self._disk_free(),
            "cb_exec_allow": self.cb_exec.allow(),
            "cb_llm_allow": self.cb_llm.allow(),
        }
        self.last_metrics = m
        return m

    def should_shed_load(self) -> bool:
        m = self.last_metrics or self.snapshot()
        if (
            (m["cpu"] >= self.cpu_high)
            or (m["ram"] >= self.ram_high)
            or (m["disk_free"] < self.disk_min_bytes)
        ):
            return True
        if not m["cb_exec_allow"] or not m["cb_llm_allow"]:
            return True
        return False

    def on_exec_fail(self):
        self.cb_exec.fail()

    def on_exec_ok(self):
        self.cb_exec.ok()

    def on_llm_fail(self):
        self.cb_llm.fail()

    def on_llm_ok(self):
        self.cb_llm.ok()
