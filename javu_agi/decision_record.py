import os, json, time, hashlib, pathlib

AUDIT_DIR = pathlib.Path("trace/decisions")
AUDIT_DIR.mkdir(parents=True, exist_ok=True)


def write(record: dict):
    # minimal schema
    schema = {"intent_id", "plan", "risk", "verdict", "world_model", "tools", "context"}
    missing = schema - set(record.keys())
    if missing:
        raise ValueError(f"DecisionRecord missing: {missing}")
    payload = json.dumps({"ts": time.time(), **record}, sort_keys=True)
    h = hashlib.sha256(payload.encode()).hexdigest()
    fname = AUDIT_DIR / f"{int(time.time()*1000)}_{h[:8]}.jsonl"
    with open(fname, "a", encoding="utf-8") as f:
        f.write(payload + "\n")
    # mirror ke WORM file (append-only)
    with open(AUDIT_DIR / "WORM.log", "ab") as f:
        f.write((payload + "|" + h + "\n").encode())
    return h
