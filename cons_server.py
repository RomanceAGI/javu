import os, threading, time
from fastapi import FastAPI, HTTPException, Header
from starlette.responses import JSONResponse
from javu_agi.memory.consolidation_scheduler import ConsolidationScheduler

API_TOKEN = os.getenv("API_TOKEN","dev")
app = FastAPI(title="consolidation")
SCHED = ConsolidationScheduler(interval_s=300, max_facts=8000)

def _auth(tok): 
    if tok != f"Bearer {API_TOKEN}": raise HTTPException(401,"unauthorized")

@app.post("/tick")
def tick(authorization: str | None = Header(None)):
    _auth(authorization)
    SCHED.tick(); return {"ok":True}

_running = False
@app.post("/start")
def start(authorization: str | None = Header(None)):
    _auth(authorization)
    global _running
    if _running: return {"ok": True, "running": True}
    def bg():
        global _running
        _running = True
        try:
            SCHED.run_forever()
        finally:
            _running = False
    threading.Thread(target=bg, daemon=True).start()
    return {"ok": True, "running": True}

@app.get("/status")
def status(): return {"running": _running}
