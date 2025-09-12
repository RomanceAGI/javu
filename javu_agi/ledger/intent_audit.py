import os, json, time, hashlib, pathlib

LEDGER_DIR = pathlib.Path("trace/ledger")
LEDGER_DIR.mkdir(parents=True, exist_ok=True)
LEDGER_FILE = LEDGER_DIR / "intent_ledger.worm"


def _hash(prev_hash, entry):
    m = hashlib.sha256()
    m.update((prev_hash or "").encode())
    m.update(json.dumps(entry, sort_keys=True).encode())
    return m.hexdigest()


def record_intent(intent_id: str, actor: str, intent: dict, context: dict):
    entry = {
        "ts": time.time(),
        "intent_id": intent_id,
        "actor": actor,
        "intent": intent,
        "context": context,
    }
    prev = None
    if LEDGER_FILE.exists():
        with open(LEDGER_FILE, "rb") as f:
            try:
                f.seek(-1024, os.SEEK_END)
            except OSError:
                f.seek(0)
            tail = f.readlines()[-1].decode()
            prev = tail.strip().split("|")[-1]
    h = _hash(prev, entry)
    line = json.dumps(entry, separators=(",", ":")) + "|" + h + "\n"
    with open(LEDGER_FILE, "ab") as f:
        f.write(line.encode())
    return h


def verify_chain():
    """Verify ledger hash-chain integrity"""
    prev = None
    with open(LEDGER_FILE, "r", encoding="utf-8") as f:
        for line in f:
            payload, h = line.strip().split("|")
            entry = json.loads(payload)
            calc = _hash(prev, entry)
            if calc != h:
                raise ValueError(f"Ledger broken at intent {entry['intent_id']}")
            prev = h
    return True
