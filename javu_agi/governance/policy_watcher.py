import os, time, threading
from pathlib import Path


class FileWatcher:
    def __init__(self, paths: list[str], on_change):
        self.paths = [Path(p) for p in paths]
        self.on_change = on_change
        self._mtimes = {p: p.stat().st_mtime if p.exists() else 0 for p in self.paths}
        self._run = False

    def start(self, interval=2.0):
        if self._run:
            return
        self._run = True
        threading.Thread(target=self._loop, args=(interval,), daemon=True).start()

    def _loop(self, interval):
        while self._run:
            try:
                changed = []
                for p in self.paths:
                    mt = p.stat().st_mtime if p.exists() else 0
                    if mt != self._mtimes.get(p, 0):
                        self._mtimes[p] = mt
                        changed.append(str(p))
                if changed:
                    try:
                        self.on_change(changed)
                    except Exception:
                        pass
            except Exception:
                pass
            time.sleep(interval)
