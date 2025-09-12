from __future__ import annotations
import os, json, time

BASE = os.getenv("METRICS_DIR", "/data/metrics")
os.makedirs(BASE, exist_ok=True)


def notify(event: str, payload: dict) -> None:
    """
    Telemetry-only: tulis ke file untuk observability (tanpa network).
    - events.jsonl : ring log event
    - events.prom  : counter per event
    """
    try:
        ts = int(time.time())
        # JSONL ringasan event
        with open(os.path.join(BASE, "events.jsonl"), "a", encoding="utf-8") as f:
            f.write(
                json.dumps(
                    {"ts": ts, "event": event, "payload": payload or {}},
                    ensure_ascii=False,
                )
                + "\n"
            )
    except Exception:
        pass
    try:
        # Prometheus-style bump counter
        with open(os.path.join(BASE, "events.prom"), "a", encoding="utf-8") as f:
            f.write(f'event_total{{name="{event}"}} 1\n')
    except Exception:
        pass
