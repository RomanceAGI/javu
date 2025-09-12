import os, json, tempfile
from pathlib import Path


class DistillIO:
    def __init__(self, base_dir="/artifacts", ts_fn=None):
        self.base = Path(base_dir) / "distill"
        self.base.mkdir(parents=True, exist_ok=True)
        for sub in ["incoming", "approved", "rejected", "shards", "reports", "tmp"]:
            (self.base / sub).mkdir(exist_ok=True)
        self.ts = ts_fn or (lambda: __import__("time").strftime("%Y-%m-%d"))

    def _path(self, kind):
        return self.base / kind / f"{self.ts()}.jsonl"

    def write_approved(self, sample: dict):
        with open(self._path("approved"), "a", encoding="utf-8") as f:
            f.write(json.dumps(sample, ensure_ascii=False) + "\n")

    def write_rejected(self, sample: dict, reason: str):
        sample = dict(sample)
        sample["reject_reason"] = reason
        with open(self._path("rejected"), "a", encoding="utf-8") as f:
            f.write(json.dumps(sample, ensure_ascii=False) + "\n")

    def write_json(self, relpath: str, obj, provenance: dict | None = None):
        rec = obj if isinstance(obj, dict) else {"obj": obj}
        if provenance:
            rec["_prov"] = provenance
        _atomic_write(
            os.path.join(self.base_dir, relpath),
            json.dumps(rec, ensure_ascii=False, indent=2),
        )

    def _atomic_write(path: str, data: str):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        d = os.path.dirname(path) or "."
        with tempfile.NamedTemporaryFile(
            "w", delete=False, dir=d, encoding="utf-8"
        ) as tmp:
            tmp.write(data)
            tmp_path = tmp.name
        os.replace(tmp_path, path)

    def append_rejected(self, user_id, prompt, text, meta, reason=""):
        return self.write_rejected(
            {"user_id": user_id, "input": prompt, "output": text, "meta": meta},
            reason=reason,
        )
