import os, json, time, hashlib


class ConsentLedger:
    def __init__(self, base_dir="/artifacts/audit/consent"):
        self.dir = base_dir
        os.makedirs(self.dir, exist_ok=True)
        self._last = None

    def _h(self, s: str) -> str:
        return hashlib.sha256(s.encode("utf-8")).hexdigest()

    def _write(self, fn: str, obj: dict):
        with open(fn, "a", encoding="utf-8") as f:
            f.write(json.dumps(obj, ensure_ascii=False) + "\n")

    def record(self, episode: str, user: str, kind: str, payload: dict):
        ts = int(time.time() * 1000)
        prev = self._last or "GENESIS"
        s = json.dumps(
            {
                "ts": ts,
                "ep": episode,
                "user": user,
                "kind": kind,
                "payload": payload,
                "prev": prev,
            },
            ensure_ascii=False,
        )
        h = self._h(s)
        self._write(
            os.path.join(self.dir, f"{time.strftime('%Y%m%d')}.jsonl"),
            {"ts": ts, "hash": h, "data": s},
        )
        self._last = h

    def verify(self, date_str: str) -> bool:
        fp = os.path.join(self.dir, f"{date_str}.jsonl")
        if not os.path.exists(fp):
            return True
        last = "GENESIS"
        for line in open(fp, "r", encoding="utf-8"):
            rec = json.loads(line)
            data = json.loads(rec["data"])
            if data["prev"] != last:
                return False
            if self._h(rec["data"]) != rec["hash"]:
                return False
            last = rec["hash"]
        return True
