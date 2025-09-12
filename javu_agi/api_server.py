import os, json, uuid, time, glob
import json as _json
from typing import Dict, Any, Optional, List, Literal

from fastapi import (
    FastAPI,
    WebSocket,
    WebSocketDisconnect,
    Depends,
    Header,
    HTTPException,
    Request,
    APIRouter,
)
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from starlette.concurrency import run_in_threadpool
from collections import deque
import threading
import contextlib

from javu_agi.config import load_router_policy
from javu_agi.safety.kill_switch import KillSwitch
from javu_agi.utils.metrics_server import serve, inc_metric, set_metric
from javu_agi.utils.degrade import enqueue_ticket, ticket_status
from javu_agi.eval.eval_harness import run_suite
from javu_agi.executive_controller import ExecutiveController
from javu_agi.learn.curriculum import build_default_curriculum
from javu_agi.learn.curriculum_runner import run_batch
from javu_agi.learn.curriculum_bank import generate as bank_generate
from javu_agi.redteam import run_redteam
from javu_agi.self_improve import propose_skill, verify_skill, register_skill
from javu_agi.fuzz import fuzz_bank
from javu_agi.bank_guard import filter_bank
from javu_agi.autonomy import AutonomyGate
from javu_agi.train_world import fit_mb_from_distill
from javu_agi.oversight_panel import build_router as build_oversight_router
from javu_agi.audit_router import router as audit_router
from javu_agi.incident_router import router as incident_router
from javu_agi.runtime.sandbox_guard import preflight
from infra.budget_state import snapshot as budget_snapshot
from scripts.repro_bundle import make_bundle as make_repro_bundle
from javu_agi.hri.dialog_policy import safe_counter

# Job status via Redis/RQ (optional)
try:
    from redis import Redis
    from rq.job import Job

    _REDIS = Redis.from_url(os.getenv("REDIS_URL", "redis://redis:6379/0"))
except Exception:
    _REDIS = None

from javu_agi.runtime.queue import enqueue


# absolute imports with graceful fallback
def _try_import(path: str):
    try:
        import importlib

        return importlib.import_module(path)
    except Exception:
        return None


ArenaExec = _try_import("javu_agi.arena.executor") or _try_import("arena.executor")
EC_mod = _try_import("javu_agi.executive_controller") or _try_import(
    "executive_controller"
)
EvalH = _try_import("javu_agi.eval_harness") or _try_import("eval_harness")

RATE_MAX_PER_MIN = int(os.getenv("RATE_MAX_PER_MIN", "120"))
_ip_lock = threading.Lock()
_ip_hits: dict[str, deque] = {}

API_KEYS = set(os.getenv("API_KEYS", "demo_key").split(","))
ADMIN_KEYS = (
    set(os.getenv("ADMIN_KEYS", "").split(",")) if os.getenv("ADMIN_KEYS") else set()
)


# ---------------- Admin auth gate ----------------
def _admin_gate(request: Request):
    key = request.headers.get("x-admin-key") or request.query_params.get("admin_key")
    if not key or key not in ADMIN_KEYS:
        raise HTTPException(401, "invalid or missing ADMIN key")
    return True


# mapping API key -> tier (bisa override via env USER_TIERS_JSON)
USER_TIER = {k: ("pro" if i > 0 else "free") for i, k in enumerate(API_KEYS)}
try:
    USER_TIER.update(_json.loads(os.getenv("USER_TIERS_JSON", "{}")))
except Exception:
    pass

# tier limits default + bisa override via TIER_LIMITS_JSON
_TIER_LIMITS_DEFAULT = {
    "free": {"rps": 1, "rpm": 60, "rph": 500, "usd_daily": 1.0},
    "plus": {"rps": 2, "rpm": 200, "rph": 2000, "usd_daily": 5.0},
    "pro": {"rps": 5, "rpm": 1000, "rph": 5000, "usd_daily": 50.0},
    "enterprise": {"rps": 10, "rpm": 5000, "rph": 50000, "usd_daily": 500.0},
}
try:
    TIER_LIMITS = _json.loads(os.getenv("TIER_LIMITS_JSON", "")) or _TIER_LIMITS_DEFAULT
except Exception:
    TIER_LIMITS = _TIER_LIMITS_DEFAULT

# ---------------- FastAPI app ----------------
app = FastAPI(title="JAVU AGI API", version="0.1.4")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_allow_origins = [
    s.strip() for s in os.getenv("ALLOW_ORIGINS", "*").split(",") if s.strip()
]


@app.middleware("http")
async def _training_blocker(request: Request, call_next):
    p = (request.url.path or "").lower()
    if p.startswith("/v0/train"):
        raise HTTPException(status_code=403, detail="training endpoints disabled")
    if p.startswith("/v0/runner") and (
        request.query_params.get("mode", "").lower() == "train"
    ):
        raise HTTPException(status_code=403, detail="training jobs disabled")
    resp = await call_next(request)
    try:
        resp.headers["X-Training-Disabled"] = "true"
        try:
            ip = request.client.host if request.client else "unknown"
            with _ip_lock:
                hits = len(_ip_hits.get(ip, []))
            resp.headers["X-RateLimit-Window"] = "60s"
            resp.headers["X-RateLimit-Used"] = str(hits)
            resp.headers["X-RateLimit-MaxPerMin"] = str(RATE_MAX_PER_MIN)
        except Exception:
            pass
    except Exception:
        pass
    return resp


_audit = _try_import("javu_agi.audit_router") or _try_import("audit_router")
if _audit and hasattr(_audit, "router"):
    app.include_router(_audit.router)

_incident = _try_import("javu_agi.incident_router") or _try_import("incident_router")
if _incident and hasattr(_incident, "router"):
    app.include_router(_incident.router)

API_TOKEN = os.getenv("API_TOKEN", "")
try:
    _EC_SINGLETON = ExecutiveController()
    app.include_router(build_oversight_router(_EC_SINGLETON.oversight_queue))
except Exception:
    pass


def _auth(x_token: str | None = Header(default=None)):
    if API_TOKEN and (x_token or "") != API_TOKEN:
        raise HTTPException(status_code=401, detail="unauthorized")
    return True


def _rate(ip: str):
    if RATE_MAX_PER_MIN <= 0:
        return
    now = time.time()
    with _ip_lock:
        dq = _ip_hits.setdefault(ip, deque())
        # drop older than 60s
        while dq and now - dq[0] > 60.0:
            dq.popleft()
        if len(dq) >= RATE_MAX_PER_MIN:
            raise HTTPException(status_code=429, detail="rate limit")
        dq.append(now)


# Admin router (kill switch & status)
admin_router = APIRouter(prefix="/admin", tags=["admin"])


@admin_router.post("/kill")
def kill(reason: str = "manual", _=Depends(_admin_gate)):
    KillSwitch.activate(reason)
    _audit_runner("admin_kill", {"reason": reason})
    return {"status": "killed", "reason": reason}


@admin_router.post("/unkill")
def unkill(_=Depends(_admin_gate)):
    KillSwitch.deactivate()
    _audit_runner("admin_unkill", {})
    return {"status": "active"}


@admin_router.get("/kill_status")
def kill_status(_=Depends(_admin_gate)):
    st = {"active": KillSwitch.is_active()}
    _audit_runner("admin_kill_status", st)
    return st


app.include_router(admin_router)


# Router hot-reload (admin)
@admin_router.post("/router/reload")
def reload_router(_=Depends(_admin_gate)):
    try:
        pol = load_router_policy()
        _EC_SINGLETON.router.load_policy(pol)
        _EC_SINGLETON.router.strict_caps = True
        return {"status": "ok", "reloaded": True}
    except Exception as e:
        raise HTTPException(500, f"router_reload_failed: {e}")


# 429 handler (rate limit)
async def http_exc_handler(request: Request, exc: HTTPException):
    if exc.status_code == 429:
        return JSONResponse(
            status_code=429,
            content={
                "error": "quota_exceeded",
                "message": str(exc.detail),
                "upgrade_url": "https://your-app.com/upgrade",
            },
        )
    return JSONResponse(
        status_code=exc.status_code, content={"detail": str(exc.detail)}
    )


app.add_exception_handler(HTTPException, http_exc_handler)

# Start Prometheus exporter
serve(
    host=os.getenv("METRICS_HOST", "0.0.0.0"),
    port=int(os.getenv("METRICS_PORT", "9200")),
)

# rate gate (RPM + USD per-user-per-day)
WINDOW = 3600
_led: Dict[str, Dict[str, int]] = {}  # dev fallback


def _incr_window(user: str, gran: str, window_s: int, limit: int) -> None:
    tsb = int(time.time() // window_s)
    if _REDIS:
        k = f"rl:{user}:{gran}:{tsb}"
        v = _REDIS.incr(k)
        _REDIS.expire(k, window_s + 5)
        if v > limit:
            raise HTTPException(429, f"rate limit exceeded ({gran})")
        return
    # fallback dev (single process)
    bucket = _led.setdefault(user, {})
    key = f"{gran}:{tsb}"
    bucket[key] = bucket.get(key, 0) + 1
    if bucket[key] > limit:
        raise HTTPException(429, f"rate limit exceeded ({gran})")
    for k2 in list(bucket.keys()):
        if not k2.endswith(str(tsb)):
            del bucket[k2]


def _user_spend_today(user: str) -> float:
    import sqlite3, os, datetime

    db = os.getenv("BUDGET_SQLITE_PATH", "/data/budget.db")
    day = datetime.date.today().isoformat()
    try:
        con = sqlite3.connect(db, timeout=2.0)
        con.execute(
            """
                    CREATE TABLE IF NOT EXISTS user_budget_daily(
                    user_id TEXT, day TEXT, spent_usd REAL NOT NULL DEFAULT 0,
                    PRIMARY KEY(user_id, day)
                    )
                    """
        )
        cur = con.execute(
            "SELECT spent_usd FROM user_budget_daily WHERE user_id=? AND day=?",
            (user, day),
        )
        row = cur.fetchone()
        con.close()
        return float(row[0]) if row else 0.0
    except Exception:
        return 0.0


# --- backpressure queue depth ---
MAX_QUEUE = int(os.getenv("QUEUE_MAX_PENDING", "200"))


def _queue_depth() -> int:
    if _REDIS:
        try:
            from rq.registry import (
                StartedJobRegistry,
                ScheduledJobRegistry,
                FailedJobRegistry,
            )
            from rq import Queue

            q = Queue(connection=_REDIS)
            n = q.count
            n += StartedJobRegistry(queue=q).count
            n += ScheduledJobRegistry(queue=q).count
            n += FailedJobRegistry(queue=q).count
            return int(n)
        except Exception:
            return 0
    # fallback: hitung file lokal jika ada
    return 0


def _queue_gate():
    if MAX_QUEUE > 0 and _queue_depth() >= MAX_QUEUE:
        raise HTTPException(429, "queue full, please retry later")


def _rate_gate(request: Request) -> str:
    key = request.headers.get("x-api-key") or request.query_params.get("api_key")
    if not key or key not in API_KEYS:
        raise HTTPException(401, "invalid or missing API key")
    tier = USER_TIER.get(key, "free")
    lim = TIER_LIMITS.get(tier, TIER_LIMITS["free"])
    usd_cap = float(lim.get("usd_daily", 1.0))
    if _user_spend_today(key) >= usd_cap:
        raise HTTPException(
            429, "quota_exceeded: daily budget for your plan is exhausted"
        )
    _incr_window(key, "1s", 1, lim.get("rps", 1))
    _incr_window(key, "60s", 60, lim.get("rpm", 60))
    _incr_window(key, "3600s", 3600, lim.get("rph", 500))


# Runner audit log
RUNNER_LOG = os.getenv("RUNNER_LOG_PATH", "logs/runner.log")
os.makedirs(os.path.dirname(RUNNER_LOG), exist_ok=True)


def _audit_runner(event: str, payload: dict):
    try:
        with open(RUNNER_LOG, "a", encoding="utf-8") as f:
            f.write(
                json.dumps(
                    {"ts": int(time.time()), "event": event, **payload},
                    ensure_ascii=False,
                )
                + "\n"
            )
    except Exception:
        pass


# DIALOG POLICY HELPER
def _apply_dialog_policy_or_none(prompt: str):
    sc = safe_counter(prompt or "")
    return (
        JSONResponse({"status": "need_clarify", "text": sc}, status_code=200)
        if sc
        else None
    )


# schemas
class ExecRequest(BaseModel):
    task: str
    input: Dict[str, Any] = Field(default_factory=dict)
    modalities: List[str] = ["text"]


class TrainKickRequest(BaseModel):
    steps: int = 100000
    mixed_modalities: List[str] = ["text", "vision", "code", "voice"]


class RunnerRequest(BaseModel):
    mode: Literal["arena", "train", "eval"]
    n: int | None = None
    steps: int | None = None
    modalities: List[str] | None = None
    save_every: int | None = None
    resume: bool = False
    write_json: str | None = None


class SubmitResult(BaseModel):
    task_id: str
    output: Dict[str, Any]
    score: Optional[float] = None


class QnaReq(BaseModel):
    query: str
    context: Optional[str] = None


class CodeReq(BaseModel):
    spec: str


class AutomateReq(BaseModel):
    goal: str
    constraints: Optional[List[str]] = None


# ---------- endpoints ----------
@app.get("/healthz")
def healthz():
    return {"ok": True, "ts": int(time.time())}


@app.get("/version")
def version():
    return {"name": "JAVU AGI API", "version": app.version}


@app.get("/readyz")
def readyz():
    # check dirs & instantiate EC ringan
    for k in ("METRICS_DIR", "RESULT_CACHE_DIR", "SKILL_CACHE_DIR"):
        d = os.getenv(k, "")
        if not d or not os.path.isdir(d):
            return {"ok": False, "reason": f"dir:{k} missing"}
    try:
        ExecutiveController()  # init saja
        return {"ok": True}
    except Exception as e:
        return {"ok": False, "reason": str(e)}


@app.post("/v0/execute_task")
async def execute_task_http(payload: ExecRequest, api_key: str = Depends(_rate_gate)):
    try:
        raw_inp = payload.input
        if isinstance(raw_inp, (dict, list)):
            import json as _json

            prompt_str = _json.dumps(raw_inp, ensure_ascii=False)[:2000]
        else:
            prompt_str = str(raw_inp)[:2000]
        sc = safe_counter(prompt_str)
        if sc:
            return JSONResponse(
                {"status": "need_clarify", "text": sc, "task": payload.task},
                status_code=200,
            )
    except Exception:
        pass
    if ArenaExec and hasattr(ArenaExec, "execute_task"):
        fn = ArenaExec.execute_task
        res = await run_in_threadpool(
            fn, payload.task, payload.input, payload.modalities
        )
        return JSONResponse(res)
    # generic EC fallback
    if not EC_mod or not hasattr(EC_mod, "ExecutiveController"):
        raise HTTPException(500, "engine unavailable")
    ctrl = EC_mod.ExecutiveController()
    if hasattr(ctrl, "execute"):
        out = await run_in_threadpool(
            ctrl.execute, payload.task, payload.input, payload.modalities
        )
    elif hasattr(ctrl, "process"):
        out = await run_in_threadpool(ctrl.process, payload.task, payload.input)
    else:
        out = {"error": "no-exec"}
    return JSONResponse(out)


@app.websocket("/v0/stream_task")
async def stream_task(ws: WebSocket):
    ip = ws.client.host if ws.client else "0.0.0.0"
    try:
        _rate(ip)
    except HTTPException:
        await ws.close(code=4429)
        return

    await ws.accept()
    try:
        auth = await ws.receive_json()
        key = auth.get("api_key")
        if not key or key not in API_KEYS:
            await ws.close(code=4401)
            return
        _rate(ip)
        task_spec = await ws.receive_json()
        task = task_spec.get("task")
        tier = USER_TIER.get(key, "free")
        lim = TIER_LIMITS.get(tier, TIER_LIMITS["free"])
        _incr_window(key, "1s", 1, lim.get("rps", 1))
        _incr_window(key, "60s", 60, lim.get("rpm", 60))
        inc_metric("ws_active", 1)
        inp = task_spec.get("input", {})
        mods = task_spec.get("modalities", ["text"])
        ctrl = (
            EC_mod
            and hasattr(EC_mod, "ExecutiveController")
            and EC_mod.ExecutiveController()
        )
        if ctrl and hasattr(ctrl, "stream_execute"):
            async for chunk in ctrl.stream_execute(task, inp, mods):
                await ws.send_text(json.dumps(chunk))
        else:
            if ArenaExec and hasattr(ArenaExec, "execute_task"):
                res = ArenaExec.execute_task(task, inp, mods)
            elif ctrl and hasattr(ctrl, "execute"):
                res = ctrl.execute(task, inp, mods)
            else:
                res = {"error": "stream not supported"}
            await ws.send_text(json.dumps(res))
    except WebSocketDisconnect:
        pass
    finally:
        try:
            inc_metric("ws_active", -1)
        except Exception:
            pass
        with contextlib.suppress(Exception):
            await ws.close()


@app.post("/v0/autonomy/enable")
def auto_enable():
    AutonomyGate().enable()
    return {"ok": True}


@app.post("/v0/autonomy/disable")
def auto_disable():
    AutonomyGate().disable()
    return {"ok": True}


@app.post("/v0/autonomy/tick")
def auto_tick():
    ec = ExecutiveController()
    return ec.tick()


@app.post("/v0/autonomy/run")
def auto_run(max_ticks: int = 10, sleep_s: float = 2.0):
    AutonomyGate().enable()
    ec = ExecutiveController()
    return ec.run_autonomy(max_ticks=max_ticks, sleep_s=sleep_s)


@app.get("/v0/metrics/daily")
def metrics_daily(api_key: str = Depends(_rate_gate)):
    p = "arena_logs/daily/latest.json"
    if not os.path.exists(p):
        return {"status": "pending"}
    with open(p) as f:
        return json.load(f)


@app.get("/v0/selfcheck")
def selfcheck():
    try:
        ec = ExecutiveController()
        resp, meta = ec.process("selfcheck", "echo hello")
        ok = bool(resp and not meta.get("blocked"))
        return {"ok": ok, "result": {"response": resp, "meta": meta}}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@app.post("/v0/train/kick")
async def kick_train(req: TrainKickRequest):
    raise HTTPException(status_code=403, detail="training disabled (vendor-only mode)")


@app.post("/v0/runner")
async def runner(req: RunnerRequest):
    if (req.mode or "").lower() == "train":
        raise HTTPException(status_code=403, detail="training jobs disabled")
    return {"ok": True, "queued": False}


@app.post("/v0/qna")
def qna(r: QnaReq, api_key: str = Depends(_rate_gate)):
    pol = _apply_dialog_policy_or_none(r.query)
    if pol is not None:
        return pol
    ec = ExecutiveController()
    resp, meta = ec.process(api_key, {"query": r.query, "context": r.context or ""})
    return JSONResponse({"response": resp, "meta": meta})


@app.post("/v0/codegen")
def codegen(r: CodeReq, api_key: str = Depends(_rate_gate)):
    pol = _apply_dialog_policy_or_none(r.spec)
    if pol is not None:
        return pol
    ec = ExecutiveController()
    resp, meta = ec.process(api_key, {"spec": r.spec})
    return JSONResponse({"response": resp, "meta": meta})


@app.post("/v0/automate")
def automate(r: AutomateReq, api_key: str = Depends(_rate_gate)):
    goal = r.goal or ""
    pol = _apply_dialog_policy_or_none(goal)
    if pol is not None:
        return pol
    ec = ExecutiveController()
    resp, meta = ec.process(
        api_key, {"goal": r.goal, "constraints": r.constraints or []}
    )
    return JSONResponse({"response": resp, "meta": meta})


@app.post("/v0/arena/submit")
def submit_arena(res: SubmitResult, api_key: str = Depends(_rate_gate)):
    _queue_gate()
    os.makedirs("arena_logs/submissions", exist_ok=True)
    path = f"arena_logs/submissions/{res.task_id}_{uuid.uuid4().hex}.json"
    with open(path, "w") as f:
        json.dump(res.dict(), f)
    return {"ok": True, "path": path}


# === TRAINING/DISTILLATION GUARD (ToS-safe) ===
try:
    from javu_agi.registry import feature_enabled
except Exception:

    def feature_enabled(_):
        return False


_TRAIN_PATH_PREFIXES = ("/v0/train", "/v0/runner", "/v0/train/kick", "/v0/train/world")


@app.get("/v0/job/{job_id}")
def job_status(job_id: str, api_key: str = Depends(_rate_gate)):
    if not _REDIS:
        raise HTTPException(500, "Redis unavailable")
    try:
        job = Job.fetch(job_id, connection=_REDIS)
        return {
            "id": job.id,
            "status": job.get_status(),
            "enqueued_at": str(job.enqueued_at) if job.enqueued_at else None,
            "started_at": str(job.started_at) if job.started_at else None,
            "ended_at": str(job.ended_at) if job.ended_at else None,
            "result": job.result if job.is_finished else None,
        }
    except Exception as e:
        raise HTTPException(404, f"job not found: {e}")


@app.post("/v0/submit")
def submit_job(req: dict, api_key: str = Depends(_rate_gate)):
    tid = enqueue_ticket(req.get("kind", "generic"), req)
    return {"ok": True, "tid": tid or ""}


@app.get("/v0/status/{tid}")
def job_status(tid: str):
    return {"tid": tid, "status": ticket_status(tid)}


@app.get("/v0/status")
def status(api_key: str = Depends(_rate_gate)):
    ec = ExecutiveController()
    snap = ec.status.snapshot()
    return {"ok": True, "status": snap}


@app.get("/metrics/files")
def list_metrics():
    import os, glob

    d = os.getenv("METRICS_DIR", "/data/metrics")
    files = [
        {"name": os.path.basename(p), "size": os.path.getsize(p)}
        for p in glob.glob(os.path.join(d, "*.prom"))
    ]
    return {"ok": True, "files": files}


@app.get("/v0/usage/me")
def usage_me(api_key: str = Depends(_rate_gate)):
    day = time.strftime("%Y-%m-%d")
    spent = _user_spend_today(api_key)
    tier = USER_TIER.get(api_key, "free")
    lim = TIER_LIMITS.get(tier, TIER_LIMITS["free"])
    if _REDIS:
        v = _REDIS.get(f"llm:budget_user:{api_key}:{day}")
        if v is not None:
            try:
                spent = float(v)
            except Exception:
                pass
    return {
        "day": day,
        "user": api_key,
        "tier": tier,
        "usd_spent_today": spent,
        "limits": lim,
    }


@app.get("/v0/eval")
def eval_suite():
    ec = ExecutiveController()
    res = run_suite(ec, user_id="bench")
    return {
        "ok": True,
        "results": [{"case": c, "ok": bool(o), "sec": float(t)} for (c, o, t) in res],
    }


@app.post("/v0/curriculum/run")
def curriculum_run(batch: int = 16):
    ec = ExecutiveController()
    try:
        if EvalH and hasattr(EvalH, "run_curriculum"):
            res = EvalH.run_curriculum(ec)
            return {
                "ok": True,
                "results": [
                    {"case": c, "ok": bool(o), "sec": float(t)} for (c, o, t) in res
                ],
            }
    except Exception:
        pass

    cur = build_default_curriculum()
    res = run_batch(ec, cur, bank=None, batch=batch)
    return {
        "ok": True,
        "stage": cur.stage,
        "results": [{"tag": t, "id": i, "ok": o, "sec": s} for (t, i, o, s) in res],
    }


@app.post("/v0/redteam/run")
def _run_redteam():
    ec = ExecutiveController()
    res = run_redteam(ec)
    return {"ok": True, **res}


@app.post("/v0/self_improve/propose")
def _propose_skill(desc: str):
    ec = ExecutiveController()
    sk = propose_skill(desc, ec.router, ec.tools)
    if not verify_skill(sk, ec):
        return {"ok": False, "reason": "verify_failed"}
    path = register_skill(sk)
    return {"ok": True, "skill_path": path, "name": sk.get("name")}


@app.post("/v0/curriculum/batch")
def curriculum_batch():
    # opsional: load bank dari file JSON kalau tersedia
    bank_path = os.getenv("CURRICULUM_BANK_JSON", "")
    bank = {}
    try:
        if bank_path and os.path.exists(bank_path):
            import json

            with open(bank_path, "r", encoding="utf-8") as f:
                bank = json.load(f)
    except Exception:
        bank = {}

    ec = ExecutiveController()
    cur = build_default_curriculum()
    res = run_batch(ec, cur, bank=bank, batch=int(os.getenv("CURRICULUM_BATCH", "8")))
    return {
        "ok": True,
        "stage": cur.stage,
        "results": [{"tag": t, "id": i, "ok": o, "sec": s} for (t, i, o, s) in res],
    }


@app.post("/v0/bank/generate")
def bank_generate_endpoint(limit: int = 500, name: str = "auto_hard.jsonl"):
    r = bank_generate(limit_sweep=limit, bank_name=name)  # miner lo
    # guard: hasil -> *.safe.jsonl
    safe_out = name.replace(".jsonl", ".safe.jsonl")
    kept = filter_bank(
        inp=os.path.join("data/task_bank", name),
        out=os.path.join("data/task_bank", safe_out),
    )
    return {"ok": True, **r, "safe_file": safe_out, "kept": kept}


@app.post("/v0/bank/fuzz")
def bank_fuzz_endpoint(
    name: str = "auto_hard.safe.jsonl",
    out_name: str = "auto_hard.fuzz.jsonl",
    n_per_case: int = 3,
):
    out = fuzz_bank(
        inp=os.path.join("data/task_bank", name),
        out=os.path.join("data/task_bank", out_name),
        n_per_case=n_per_case,
    )
    return {"ok": True, **out}


@app.post("/v0/train/world")
def world_train(req: dict):
    raise HTTPException(status_code=403, detail="training disabled (vendor-only mode)")


@app.post("/v0/proofs/run")
def proofs_run(batch: int = 16):
    ec = ExecutiveController()
    cur = build_default_curriculum()
    # 1) jalankan batch kurikulum
    cur_res = run_batch(ec, cur, bank=None, batch=batch)
    # 2) redteam kecil (pakai yang sudah ada /v0/redteam/run kalau lo bikin)
    try:
        from javu_agi.redteam import run_redteam

        rt = run_redteam(ec)
    except Exception:
        rt = {}
    return {
        "ok": True,
        "curriculum": [
            {"tag": t, "id": i, "ok": o, "sec": s} for (t, i, o, s) in cur_res
        ],
        "redteam": rt,
    }


@app.get("/admin/budget_state")
def budget_state():
    from javu_agi.executive_controller import ExecutiveController

    ec = getattr(app.state, "ec", None) or ExecutiveController()
    app.state.ec = ec
    return budget_snapshot(ec)


@app.get("/admin/repro_bundle")
def repro_bundle(request: Request):
    trace_id = request.query_params.get("trace_id") or str(int(time.time()))
    try:
        path = make_repro_bundle(trace_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"bundle error: {e}")
    if not path or not os.path.exists(path):
        raise HTTPException(status_code=500, detail="bundle not created")
    return FileResponse(path, filename=os.path.basename(path))


@app.get("/debug/status")
def debug_status():
    import psutil

    mem = psutil.virtual_memory()._asdict()
    audit_dir = os.getenv("AUDIT_DIR", "artifacts/audit_chain")
    trans_log = os.getenv("TRANSPARENCY_LOG", "artifacts/transparency.jsonl")
    last_audit = []
    try:
        for f in sorted(glob.glob(os.path.join(audit_dir, "*.jsonl")))[-3:]:
            with open(f, "r", encoding="utf-8") as fh:
                last_audit += fh.readlines()[-5:]
    except Exception:
        pass
    last_transparency = []
    try:
        if os.path.exists(trans_log):
            with open(trans_log, "r", encoding="utf-8") as fh:
                last_transparency = fh.readlines()[-5:]
    except Exception:
        pass
    return JSONResponse(
        {
            "mem": mem,
            "env_flags": {
                "DEV_FAST": os.getenv("DEV_FAST", "0"),
                "KILL_SWITCH": os.getenv("KILL_SWITCH", "0"),
            },
            "last_audit": last_audit,
            "last_transparency": last_transparency,
        }
    )


@app.get("/admin/planetary_state")
def planetary_state():
    try:
        ec = ExecutiveController()
        guard = getattr(ec, "sustainability", None)
        if not guard:
            return JSONResponse({"enabled": False})
        pol = guard.policy
        return JSONResponse(
            {
                "enabled": True,
                "ledger": guard.ledger,
                "policy": {
                    "max_co2e_day": pol.max_co2e_day,
                    "max_water_m3_day": pol.max_water_m3_day,
                    "biodiversity_veto": pol.biodiversity_veto,
                    "social_risk_max": pol.social_risk_max,
                    "sector_caps": pol.sector_caps,
                },
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/statusz")
def statusz(request: Request):
    ip = request.client.host if request.client else "-"
    return {
        "ts": datetime.utcnow().isoformat() + "Z",
        "ip": ip,
        "queue_depth": _queue_depth(),
        "killswitch": KillSwitch.is_active(),
        "rate_max_per_min": RATE_MAX_PER_MIN,
    }


@app.get("/v0/evidence/export")
def export_evidence(_=Depends(_auth)):
    try:
        bundle_path = make_repro_bundle(out_dir=os.getenv("ARTIFACTS_DIR", "artifacts"))
    except Exception as e:
        raise HTTPException(500, f"repro_bundle_failed: {e}")
    ac_dir = os.getenv("AUDIT_CHAIN_DIR", "/data/audit_chain")
    try:
        os.makedirs(ac_dir, exist_ok=True)
    except Exception:
        pass
    info = {
        "repro_bundle": bundle_path,
        "audit_chain_dir": ac_dir,
    }
    return JSONResponse(info)
