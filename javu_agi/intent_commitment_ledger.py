import hashlib, json, time, os, pathlib

LEDGER_DIR = pathlib.Path("trace/ledger")
LEDGER_DIR.mkdir(parents=True, exist_ok=True)
LEDGER_FILE = LEDGER_DIR / "intent_ledger.worm"


def _hash(prev_hash, entry):
    m = hashlib.sha256()
    m.update((prev_hash or "").encode())
    m.update(json.dumps(entry, sort_keys=True).encode())
    return m.hexdigest()


def append_intent(intent_id: str, actor: str, intent: dict, context: dict):
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
            f.seek(-65, os.SEEK_END)
            prev = f.read(64).decode()  # tail hash
    h = _hash(prev, entry)
    line = json.dumps(entry, separators=(",", ":")) + "|" + h + "\n"
    with open(LEDGER_FILE, "ab") as f:
        f.write(line.encode())
    return h
