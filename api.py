from __future__ import annotations
import os, time, uuid, json
from typing import Optional
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.concurrency import run_in_threadpool
from pydantic import BaseModel, Field

from javu_agi.user_loop import run_user_loop

APP_NAME = os.getenv("APP_NAME", "javu-agi")
MAX_INPUT_LEN = int(os.getenv("API_MAX_INPUT_LEN", "8000"))

app = FastAPI(title=APP_NAME)

# Optional CORS (aktifkan kalau perlu)
if os.getenv("API_CORS_ALLOW_ALL", "0") == "1":
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"], allow_credentials=False,
        allow_methods=["*"], allow_headers=["*"],
    )

class InputData(BaseModel):
    user_id: str = Field(..., min_length=1, max_length=128)
    user_input: str = Field(..., min_length=1)

class OutputData(BaseModel):
    response: str
    latency_ms: int
    request_id: str

@app.middleware("http")
async def add_request_id_logging(request: Request, call_next):
    rid = request.headers.get("x-request-id") or str(uuid.uuid4())
    start = time.time()
    try:
        resp = await call_next(request)
        return resp
    finally:
        dur = int((time.time() - start) * 1000)
        # Log JSON ke stdout (dipungut Docker)
        log = {
            "ts": int(time.time()),
            "level": "INFO",
            "evt": "http",
            "path": str(request.url.path),
            "method": request.method,
            "latency_ms": dur,
            "request_id": rid,
        }
        print(json.dumps(log, ensure_ascii=False))

@app.exception_handler(Exception)
async def unhandled_exc(_: Request, exc: Exception):
    print(json.dumps({"level":"ERROR","evt":"exception","err":str(exc)}, ensure_ascii=False))
    return JSONResponse(status_code=500, content={"detail": "internal_error"})

@app.get("/healthz")
async def healthz():
    return {"status": "ok"}

@app.post("/interact", response_model=OutputData)
async def interact(data: InputData, request: Request):
    if len(data.user_input) > MAX_INPUT_LEN:
        raise HTTPException(status_code=413, detail="input_too_large")
    request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
    try:
        result = await run_in_threadpool(run_user_loop, data.user_id, data.user_input)
        out = {
            "response": result or "",
            "latency_ms": 0,  # diisi oleh middleware log; opsional isi real di sini
            "request_id": request_id,
        }
        return out
    except HTTPException:
        raise
    except Exception as e:
        print(json.dumps({"level":"ERROR","evt":"interact_fail","err":str(e)}, ensure_ascii=False))
        raise HTTPException(status_code=500, detail="internal_error")

