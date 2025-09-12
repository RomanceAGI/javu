import os, json, random, time
from pathlib import Path
from typing import List, Dict, Any

OUT_DIR = "arena_logs/memory"
os.makedirs(OUT_DIR, exist_ok=True)

def _try_import(p):
    """Attempt to import a module by name, returning None on failure.

    Only ImportError is caught so that unexpected exceptions are not silently
    suppressed.
    """
    try:
        return __import__(p, fromlist=["*"])
    except ImportError:
        return None

Mem = _try_import("javu_agi.memory.memory")

def gen_kvpairs(n=200) -> List[Dict[str, str]]:
    return [{"k": f"key_{i}", "v": f"value_{i}_{random.randint(1000,9999)}"} for i in range(n)]

def write_phase(pairs):
    for p in pairs:
        # adapt ke API memory lo
        if hasattr(Mem, "write"):
            Mem.write(p["k"], p["v"])
        else:
            pass

def read_phase(pairs, k=5):
    hits = 0
    for p in pairs:
        if hasattr(Mem, "retrieve"):
            res = Mem.retrieve(p["k"], topk=k)  # -> list
            vals = [r.get("value") if isinstance(r, dict) else str(r) for r in (res or [])]
            if any(p["v"] in v for v in vals):
                hits += 1
    return hits / max(1, len(pairs))

def interference_phase(n_topics=5, per_topic=40):
    topics = [f"topic_{i}" for i in range(n_topics)]
    pairs = []
    for t in topics:
        pairs += [{"k": f"{t}:{i}", "v": f"{t}_val_{i}"} for i in range(per_topic)]
    write_phase(pairs)
    # shuffle & read
    random.shuffle(pairs)
    return read_phase(pairs, k=3)

def run_eval():
    base = gen_kvpairs(200)
    write_phase(base)
    recall = read_phase(base, k=5)
    interference = interference_phase()
    out = {
        "ts": int(time.time()),
        "recall@5": recall,
        "interference": interference,
        "n": len(base)
    }
    Path(f"{OUT_DIR}/latest.json").write_text(json.dumps(out, indent=2))
    print(json.dumps(out, indent=2))

if __name__ == "__main__":
    run_eval()
