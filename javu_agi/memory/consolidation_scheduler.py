from __future__ import annotations
import time
from typing import Optional
from memory.consolidation import Consolidator


class ConsolidationScheduler:
    """
    Jalankan konsolidasi episodik → semantik secara periodik + forgetting.
    Bisa dipanggil di background thread / service terpisah nanti di VPS.
    """

    def __init__(self, interval_s: int = 300, max_facts: int = 5000):
        self.interval_s = interval_s
        self.max_facts = max_facts
        self.cons = Consolidator()
        self._stop = False

    def _forget(self):
        import json, os

        path = "data/memory/semantic.json"
        if not os.path.exists(path):
            return
        data = json.load(open(path, "r", encoding="utf-8"))
        if len(data) <= self.max_facts:
            return
        # simple LRU-ish: urutkan paling lama → potong
        data.sort(key=lambda x: x.get("timestamp", ""))
        keep = data[-self.max_facts :]
        json.dump(keep, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

    def tick(self):
        self.cons.run()
        self._forget()

    def run_forever(self):
        while not self._stop:
            self.tick()
            time.sleep(self.interval_s)

    def stop(self):
        self._stop = True
