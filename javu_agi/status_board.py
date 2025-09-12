from __future__ import annotations
import time
from collections import deque
from typing import Dict, Deque, Tuple


class StatusBoard:
    def __init__(self, window: int = 100):
        self.window = window
        self.latencies: Deque[float] = deque(maxlen=window)
        self.blocks: Deque[str] = deque(maxlen=window)  # reasons
        self.plans: Deque[Tuple[float, int]] = deque(maxlen=window)  # (ts, steps)
        self.domains: Deque[str] = deque(maxlen=window)

    def record(self, meta: Dict):
        if "latency_s" in meta:
            self.latencies.append(float(meta["latency_s"]))
        if meta.get("blocked"):
            self.blocks.append(meta.get("reason", "unknown"))
        if "domains" in meta:
            for d in meta["domains"]:
                self.domains.append(str(d))
        if "plan_steps" in meta and "episode_ts" in meta:
            self.plans.append((float(meta["episode_ts"]), int(meta["plan_steps"])))

    def snapshot(self) -> Dict:
        n = max(1, len(self.latencies))
        return {
            "avg_latency_s": round(sum(self.latencies) / n, 3),
            "p95_latency_s": (
                sorted(self.latencies)[int(0.95 * (n - 1))]
                if n > 1
                else (self.latencies[-1] if self.latencies else 0)
            ),
            "blocked_recent": list(self.blocks),
            "domains_recent": list(self.domains)[-10:],
            "plans_recent": len(self.plans),
        }
