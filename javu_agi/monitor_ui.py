from fastapi import FastAPI
import os, json, time

app = FastAPI()
M = {"requests_total": 0, "blocked_ethics_total": 0, "latency_ms_p95": 0}


@app.get("/health")
def health():
    return {"status": "ok", "ts": int(time.time())}


@app.get("/metrics")
def metrics():
    return M


@app.get("/logs/decisions")
def decisions():
    path = os.getenv("DECISION_LOG", "./logs/decisions.jsonl")
    try:
        with open(path, encoding="utf-8") as f:
            return [json.loads(l) for l in f.readlines()[-50:]]
    except Exception:
        return []
