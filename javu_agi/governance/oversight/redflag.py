import json, os, time, pathlib

OUT = os.getenv("GOV_REPORT_DIR", "artifacts/governance/reports")
pathlib.Path(OUT).mkdir(parents=True, exist_ok=True)


def report(event_type: str, payload: dict):
    row = {"ts": int(time.time()), "type": event_type, "payload": payload}
    with open(
        os.path.join(OUT, f"{time.strftime('%Y%m%d')}_redflags.jsonl"),
        "a",
        encoding="utf-8",
    ) as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")
    return row
