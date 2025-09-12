from __future__ import annotations
from fastapi import APIRouter
from fastapi.responses import JSONResponse, HTMLResponse
import os, glob, json

router = APIRouter(prefix="/audit", tags=["audit"])

XAI_DIR = os.getenv("XAI_DIR", "artifacts/xai")


@router.get("/list")
def list_reports(limit: int = 20):
    """List XAI reports (HTML files) saved by explain_ui."""
    try:
        files = sorted(
            glob.glob(f"{XAI_DIR}/*.html"), key=os.path.getmtime, reverse=True
        )
        return {"status": "ok", "files": files[:limit]}
    except Exception as e:
        return {"status": "error", "reason": str(e)}


@router.get("/report/{trace_id}")
def get_report(trace_id: str):
    """Return raw HTML of a given trace_id (saved by explain_ui.write)."""
    try:
        path = f"{XAI_DIR}/{trace_id}.html"
        if not os.path.exists(path):
            return JSONResponse(
                {"status": "error", "reason": "not_found"}, status_code=404
            )
        with open(path, "r", encoding="utf-8") as f:
            html = f.read()
        return HTMLResponse(html)
    except Exception as e:
        return JSONResponse({"status": "error", "reason": str(e)}, status_code=500)


@router.get("/json/{trace_id}")
def get_json(trace_id: str):
    """Return parsed JSON from explain_reporter if saved in .jsonl."""
    try:
        jfile = f"artifacts/xai/{trace_id}.jsonl"
        if not os.path.exists(jfile):
            return JSONResponse(
                {"status": "error", "reason": "not_found"}, status_code=404
            )
        with open(jfile, "r", encoding="utf-8") as f:
            lines = [json.loads(l) for l in f]
        return {"status": "ok", "data": lines}
    except Exception as e:
        return {"status": "error", "reason": str(e)}
