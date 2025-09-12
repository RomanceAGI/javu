import os, time, threading
from collections import defaultdict


def _today_key():
    return time.strftime("%Y%m%d")


def _hour_key():
    return time.strftime("%Y%m%d%H")


class DPBudget:
    """
    Differential Privacy (approx) budget tracker:
    - daily epsilon cap
    - hourly cap
    - per-category caps (search, db, vision, etc.)
    """

    def __init__(
        self, daily: float = 1.0, hourly: float = 0.25, categories: dict | None = None
    ):
        self.daily_cap = float(os.getenv("DP_EPS_DAILY", str(daily)))
        self.hourly_cap = float(os.getenv("DP_EPS_HOURLY", str(hourly)))
        self.cat_cap = {k: float(v) for k, v in (categories or {}).items()}
        self.lock = threading.Lock()
        self._reset()

    def _reset(self):
        self.day = _today_key()
        self.hour = _hour_key()
        self.used_daily = 0.0
        self.used_hourly = 0.0
        self.used_cat = defaultdict(float)

    def _roll_windows(self):
        td, th = _today_key(), _hour_key()
        if td != self.day:
            self.day = td
            self.used_daily = 0.0
            self.used_cat.clear()
        if th != self.hour:
            self.hour = th
            self.used_hourly = 0.0

    def allow(self, cost: float, category: str | None = None) -> bool:
        with self.lock:
            self._roll_windows()
            if self.used_daily + cost > self.daily_cap:
                return False
            if self.used_hourly + cost > self.hourly_cap:
                return False
            if category and category in self.cat_cap:
                if self.used_cat[category] + cost > self.cat_cap[category]:
                    return False
            self.used_daily += cost
            self.used_hourly += cost
            if category:
                self.used_cat[category] += cost
            return True
