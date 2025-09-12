import os, json, time, hashlib


class DistillDeduper:
    def __init__(
        self, base_dir: str, window_days: int = 7, fname: str = "dedup_index.jsonl"
    ):
        self.base_dir = base_dir
        self.window_days = int(window_days)
        self.path = os.path.join(base_dir, fname)
        os.makedirs(base_dir, exist_ok=True)

    def _now(self):
        return int(time.time())

    def _key(self, prompt: str, output: str) -> str:
        h = hashlib.sha256()
        h.update((prompt or "").encode("utf-8"))
        h.update(b"\n---\n")
        h.update((output or "").encode("utf-8"))
        return h.hexdigest()

    def seen(self, prompt: str, output: str) -> bool:
        key = self._key(prompt, output)
        cutoff = self._now() - self.window_days * 86400
        if not os.path.exists(self.path):
            return False
        keep_lines, found = [], False
        with open(self.path, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    obj = json.loads(line)
                except Exception:
                    continue
                ts = int(obj.get("ts", 0))
                if ts >= cutoff:
                    keep_lines.append(line)
                if obj.get("key") == key:
                    found = True
        # compact file
        with open(self.path, "w", encoding="utf-8") as f:
            for line in keep_lines:
                f.write(line)
        return found

    def mark(self, prompt: str, output: str, meta=None) -> str:
        key = self._key(prompt, output)
        row = {"ts": self._now(), "key": key, "meta": meta or {}}
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(row) + "\n")
            f.flush()
            os.fsync(f.fileno())
        return key

    def seen(*a, **k):
        raise RuntimeError(
            "distill deduper disabled (no vendor-output dataset allowed)"
        )

    def mark(*a, **k):
        raise RuntimeError(
            "distill deduper disabled (no vendor-output dataset allowed)"
        )
