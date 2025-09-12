import os, json, time, hashlib, threading


class AuditChain:
    def __init__(self, log_dir: str):
        self.log_dir = log_dir
        os.makedirs(self.log_dir, exist_ok=True)
        self.head_path = os.path.join(self.log_dir, "audit_head.txt")
        self.lock = threading.Lock()
        self.observers = []
        if not os.path.exists(self.head_path):
            with open(self.head_path, "w", encoding="utf-8") as f:
                f.write("GENESIS")

    def subscribe(self, cb):
        self.observers.append(cb)

    def _head(self) -> str:
        try:
            with open(self.head_path, "r", encoding="utf-8") as f:
                return f.read().strip()
        except Exception:
            return "GENESIS"

    def _set_head(self, h: str):
        with open(self.head_path, "w", encoding="utf-8") as f:
            f.write(h)

    def append(self, kind: str, payload: dict) -> dict:
        with self.lock:
            head = self._head()
            rec = {"ts": int(time.time()), "kind": kind, **(payload or {})}
            raw = json.dumps(rec, ensure_ascii=False, sort_keys=True)
            h = hashlib.sha256((head + raw).encode("utf-8")).hexdigest()
            fn = os.path.join(self.log_dir, f"{time.strftime('%Y%m%d')}.jsonl")
            with open(fn, "a", encoding="utf-8") as f:
                f.write(
                    json.dumps(
                        {"hash": h, "prev": head, "record": rec}, ensure_ascii=False
                    )
                    + "\n"
                )
            self._set_head(h)
            return {"hash": h, "prev": head}

    def commit(self, kind: str, record: dict) -> dict:
        return self.append(kind, record)

    def verify(self, date_str: str) -> bool:
        fn = os.path.join(self.log_dir, f"{date_str}.jsonl")
        try:
            head = "GENESIS"
            with open(fn, "r", encoding="utf-8") as f:
                for line in f:
                    obj = json.loads(line)
                    raw = json.dumps(obj["record"], ensure_ascii=False, sort_keys=True)
                    expect = hashlib.sha256((head + raw).encode("utf-8")).hexdigest()
                    if obj["hash"] != expect:
                        return False
                    head = obj["hash"]
            return True
        except Exception:
            return False
