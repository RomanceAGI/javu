import os, json, time, uuid


class Telemetry:
    def __init__(self, base_dir: str):
        d = os.path.join(base_dir, "telemetry")
        os.makedirs(d, exist_ok=True)
        self.path = os.path.join(d, "events.jsonl")

    def emit(self, kind: str, payload: dict):
        try:
            with open(self.path, "a", encoding="utf-8") as f:
                f.write(
                    json.dumps(
                        {
                            "ts": int(time.time() * 1000),
                            "kind": kind,
                            **(payload or {}),
                        },
                        ensure_ascii=False,
                    )
                    + "\n"
                )
        except Exception:
            pass


def new_ids():
    eid = uuid.uuid4().hex[:12]
    tid = uuid.uuid4().hex[:12]
    return eid, tid
