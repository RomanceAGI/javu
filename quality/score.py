from __future__ import annotations
import os, json, time, hashlib

LOG = os.getenv("QUALITY_LOG", "logs/quality.jsonl")
os.makedirs(os.path.dirname(LOG), exist_ok=True)

def _hash(s: str) -> str:
    import hashlib
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

def log_quality(kind: str, meta: dict, content: str, score: float, warnings: list[str]):
    row = {
        "ts": int(time.time()),
        "kind": kind,
        "meta": meta,
        "score": float(score),
        "warnings": warnings,
        "content_sha256": _hash(content)[:16],
    }
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")
