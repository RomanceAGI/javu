from __future__ import annotations
from fastapi import APIRouter
from fastapi.responses import JSONResponse
import os, json, time

router = APIRouter(prefix="/incident", tags=["incident"])
BASE = os.getenv("INCIDENT_DIR", "artifacts/incidents")
os.makedirs(BASE, exist_ok=True)


@router.post("/raise")
def raise_incident(
    kind: str, severity: str = "low", message: str = "", trace_id: str | None = None
):
    try:
        rec = {
            "ts": int(time.time()),
            "kind": kind,
            "severity": severity,
            "message": message,
            "trace": trace_id,
        }
        with open(os.path.join(BASE, "incidents.jsonl"), "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        return {"status": "ok"}
    except Exception as e:
        return JSONResponse({"status": "error", "reason": str(e)}, status_code=500)


@router.get("/list")
def list_incidents(limit: int = 100):
    path = os.path.join(BASE, "incidents.jsonl")
    if not os.path.exists(path):
        return {"status": "ok", "data": []}
    out = []
    with open(path, "r", encoding="utf-8") as f:
        for line in reversed(list(f)):
            if not line.strip():
                continue
            try:
                out.append(json.loads(line))
            except Exception:
                continue
            if len(out) >= limit:
                break
    return {"status": "ok", "data": out}
