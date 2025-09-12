import os, json, heapq, time
from pathlib import Path


class PrioritizedReplay:
    def __init__(self, base=os.getenv("ARTIFACTS_DIR", "/artifacts"), cap=5000):
        self.dir = str(Path(base) / "replay")
        Path(self.dir).mkdir(parents=True, exist_ok=True)
        self.cap = cap
        self.heap = []  # ( -priority, ts, path )

    def add(*a, **k):
        raise RuntimeError("replay disabled: builder OFF")

    def sample(*a, **k):
        raise RuntimeError("replay disabled: builder OFF")
