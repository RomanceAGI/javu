from __future__ import annotations
import json, os, time, uuid


class Replay:
    def __init__(self, dirpath=os.getenv("REPLAY_DIR", "/data/replay")):
        self.dir = dirpath
        os.makedirs(self.dir, exist_ok=True)

    def record(self, tag: str, obj: dict):
        rid = str(uuid.uuid4())[:8]
        fp = os.path.join(self.dir, f"{int(time.time()*1000)}_{tag}_{rid}.json")
        try:
            json.dump(obj, open(fp, "w"), ensure_ascii=False, indent=2)
        except Exception:
            pass

    def load(self, path: str) -> dict:
        try:
            return json.load(open(path))
        except Exception:
            return {}
