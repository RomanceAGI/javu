from __future__ import annotations
import os, json, time

from javu_agi.utils.logging_config import get_logger, redact
from javu_agi.utils.atomic_write import append_jsonl_atomic

logger = get_logger("javu_agi.telemetry")

BASE = os.getenv("METRICS_DIR", "/data/metrics")
os.makedirs(BASE, exist_ok=True)


def notify(event: str, payload: dict) -> None:
    """
    Telemetry-only: tulis ke file untuk observability (tanpa network).
    - events.jsonl : ring log event
    - events.prom  : counter per event
    """
    ts = int(time.time())
    safe_payload = redact(payload or {})
    try:
        line = json.dumps({"ts": ts, "event": event, "payload": safe_payload}, ensure_ascii=False)
        append_jsonl_atomic(os.path.join(BASE, "events.jsonl"), line)
    except Exception:
        logger.exception("notify: failed writing events.jsonl for event %s", event)
    try:
        # simple prom-style increment (not atomic across processes, but append-safe)
        prom_line = f'event_total{{name="{event}"}} 1\n'
        append_jsonl_atomic(os.path.join(BASE, "events.prom"), prom_line)
    except Exception:
        logger.exception("notify: failed writing events.prom for event %s", event)