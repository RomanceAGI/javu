import json, time, os
from pathlib import Path

OUT = os.getenv("DISTILL_DIR", "artifacts/distill")
Path(OUT).mkdir(parents=True, exist_ok=True)


def log_teacher(sample):
    with open(f"{OUT}/{int(time.time()*1000)}.json", "w") as f:
        json.dump(sample, f, ensure_ascii=False)
