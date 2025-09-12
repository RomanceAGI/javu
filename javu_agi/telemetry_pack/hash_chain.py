import os, json, hashlib
from pathlib import Path


class HashChain:
    def __init__(self, dir=os.getenv("METRICS_DIR", "/data/metrics")):
        self.path = str(Path(dir) / "tamper_chain.sha")
        Path(dir).mkdir(parents=True, exist_ok=True)

    def _last(self) -> str:
        if not os.path.isfile(self.path):
            return ""
        return open(self.path, "r", encoding="utf-8").read().strip()

    def append(self, episode_digest: str) -> str:
        seed = self._last().encode("utf-8")
        h = hashlib.sha256(seed + (episode_digest or "").encode("utf-8")).hexdigest()
        with open(self.path, "w", encoding="utf-8") as f:
            f.write(h + "\n")
        return h
