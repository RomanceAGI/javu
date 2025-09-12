from __future__ import annotations
import os, time, json, hashlib, math, random, pathlib, requests, subprocess, threading, yaml
from typing import Optional, Dict, Any, List, Tuple

from pathlib import Path
from javu_agi.config import load_models_cfg, load_router_policy
from javu_agi.utils.degrade import text_image_stub, subtitles_from_text, text_slideshow_video, enqueue_ticket

# ====== CONFIG (ENV) ======
PROVIDERS = [s.strip() for s in os.getenv("PROVIDERS", "openai,anthropic").split(",") if s.strip()]
API_BUDGET_USD_DAILY = float(os.getenv("API_BUDGET_USD_DAILY", "50"))
BUDGET_SCOPE = "user"
CACHE_TTL = int(os.getenv("LLM_CACHE_TTL", "86400"))
ROUTER_LOGGING_ENABLED = os.getenv("ROUTER_LOGGING_ENABLED", "1") in {"1","true","yes"}
USAGE_LOG_PATH = os.getenv("USAGE_LOG_PATH", "logs/model_usage.jsonl")
DISTILL_DIR = os.getenv("DISTILL_DIR", "artifacts/distill")
REDIS_URL = os.getenv("REDIS_URL")  # optional caching/rate-limit
HIDE_CAP_ERRORS = os.getenv("HIDE_CAP_ERRORS","true").lower()=="true"
ROUTER_DISTILL_LOG = os.getenv("ROUTER_DISTILL_LOG","false").lower() in {"1","true","yes"}

# === media config ===
TTS_CACHE_DIR = os.getenv("TTS_CACHE_DIR", "artifacts/tts_cache")
IMG_CACHE_DIR = os.getenv("IMG_CACHE_DIR", "artifacts/img_cache")
ELEVEN_VOICE_ID = os.getenv("ELEVEN_VOICE_ID", "Rachel")

# === video storyboard config ===
VIDEO_FRAMES = int(os.getenv("VIDEO_FRAMES", "8"))
VIDEO_FPS    = int(os.getenv("VIDEO_FPS", "6"))
VIDEO_SIZE   = os.getenv("VIDEO_SIZE", "1024x1024")
VIDEO_OUT_DIR= os.getenv("VIDEO_OUT_DIR", "artifacts/video_cache")

# ====== COST TABLE (aproksimasi; isi sesuai plan harga lo) ======
# cost per 1M tokens (in/out) – sesuaikan dengan provider terbaru
MODEL_COST_USD = {
    "gpt-5":       {"in": 15.0, "out": 60.0},
    "gpt-4o":      {"in": 5.0,  "out": 15.0},
    "gpt-5-mini":  {"in": 1.5,  "out": 6.0},
    "gpt-5-nano":  {"in": 0.3,  "out": 1.2},
    "claude-opus-3": {"in": 15.0, "out": 75.0},
    "claude-sonnet-3.5": {"in": 3.0, "out": 15.0},
}

LOCAL_REG = list()  # simple runtime cache
try:
    regp = Path(os.getenv("AUTOTRAIN_OUT","artifacts/autotrain")) / "registry.jsonl"
    if regp.exists():
        for line in regp.read_text().splitlines():
            if line.strip():
                import json as _json; LOCAL_REG.append(_json.loads(line))
except Exception:
    pass

# ====== CAPABILITIES + POLICY ======
MODEL_META: Dict[str, Dict] = {
    "gpt-5":       {"ctx": 200_000, "vision": True,  "audio": True,  "tools": True,  "provider": "openai"},
    "gpt-4o":      {"ctx": 128_000, "vision": True,  "audio": True,  "tools": True,  "provider": "openai"},
    "gpt-5-mini":  {"ctx": 64_000,  "vision": True,  "audio": True,  "tools": True,  "provider": "openai"},
    "gpt-5-nano":  {"ctx": 16_000,  "vision": False, "audio": False, "tools": False, "provider": "openai"},
    "claude-opus-3": {"ctx": 200_000, "vision": True, "audio": True, "tools": True, "provider": "anthropic"},
    "claude-sonnet-3.5": {"ctx": 200_000, "vision": True, "audio": True, "tools": True, "provider": "anthropic"},
    "dall-e-3":     {"ctx": None, "vision": True,  "audio": False, "tools": False, "provider": "openai_image"},
    "elevenlabs-tts":{"ctx": None, "vision": False, "audio": True,  "tools": False, "provider": "elevenlabs"},
    "storyboard-video":{"ctx": None, "vision": True,  "audio": True,  "tools": False, "provider": "local_video"},
    # local fine-tuned checkpoints
    "local-7b": {"ctx": 131072, "vision": False, "audio": False, "tools": True, "provider": "local"},
    "local-13b":{"ctx": 131072, "vision": False, "audio": False, "tools": True, "provider": "local"},
}

# policy: route by task + fallback
LLM_DEFAULT_MODEL = os.getenv("LLM_DEFAULT_MODEL", "gpt-4o")
LLM_POLICY = {
    "route_by_task": {
        "code": os.getenv("POLICY_CODE", "gpt-5"),
        "reasoning": os.getenv("POLICY_REASONING", "gpt-5"),
        "vision": os.getenv("POLICY_VISION", "gpt-4o"),
        "voice": os.getenv("POLICY_VOICE", "gpt-4o"),
        "default": LLM_DEFAULT_MODEL,
    },
    "fallback_order": [m.strip() for m in os.getenv("POLICY_FALLBACK", "gpt-5,gpt-4o,claude-opus-3,claude-sonnet-3.5,gpt-5-mini").split(",")]
}

# === Provider daily caps (fixed keys) ===
PROVIDER_CAP = {
    "openai":        float(os.getenv("PROVIDER_CAP_OPENAI_USD_DAILY", "1e9")),
    "anthropic":     float(os.getenv("PROVIDER_CAP_ANTHROPIC_USD_DAILY", "1e9")),
    "openai_image":  float(os.getenv("PROVIDER_CAP_OPENAI_IMAGE_USD_DAILY", "1e9")),  # was 'dalle'
    "elevenlabs":    float(os.getenv("PROVIDER_CAP_ELEVENLABS_USD_DAILY", "1e9")),
    "local_video":   float(os.getenv("PROVIDER_CAP_LOCAL_VIDEO_USD_DAILY", "1e9")),   # was 'video'
}

def provider_spend_inc(provider: str, delta: float) -> float:
    day = time.strftime("%Y-%m-%d")
    if _redis:
        k = f"llm:budget:{provider}:{day}"
        cur = _redis.incrbyfloat(k, delta); _redis.expire(k, 86400)
        return float(cur)
    _budget_state[f"{provider}_total"] = _budget_state.get(f"{provider}_total", 0.0) + delta
    return _budget_state[f"{provider}_total"]

def provider_spend_get(provider: str) -> float:
    day = time.strftime("%Y-%m-%d")
    if _redis:
        v = _redis.get(f"llm:budget:{provider}:{day}")
        return float(v) if v else 0.0
    return float(_budget_state.get(f"{provider}_total", 0.0))

def _provider_overcap(model: str) -> bool:
    prov = MODEL_META.get(model, {}).get("provider")
    return prov and provider_spend_get(prov) >= PROVIDER_CAP.get(prov, 1e18)

# ====== USER OVERRIDE ======
_USER_MODEL_OVERRIDE: Dict[str, str] = {}

def set_default_model(model: str):
    global LLM_DEFAULT_MODEL
    LLM_DEFAULT_MODEL = model

def switch_llm_model(user_id: str, model: str):
    _USER_MODEL_OVERRIDE[user_id] = model

# ====== HELPERS ======
import unicodedata, re

def _supports(modalities: Optional[set], model: str) -> bool:
    if not modalities: return True
    caps = MODEL_META.get(model, {})
    return all(caps.get(m, False) for m in modalities)

def _json_safe(obj: Any) -> Any:
    """Best-effort to convert to JSON-serializable."""
    try:
        json.dumps(obj, ensure_ascii=False)
        return obj
    except Exception:
        if isinstance(obj, dict):
            return {str(k): _json_safe(v) for k,v in obj.items()}
        if isinstance(obj, (list, tuple, set)):
            return [_json_safe(x) for x in obj]
        return str(obj)

def _hash_payload(obj: Any) -> str:
    return hashlib.sha256(json.dumps(_json_safe(obj), sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()

def _log_jsonl(path: str, row: Dict[str, Any]):
    if not ROUTER_LOGGING_ENABLED:
        return
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")

def _now_s() -> int:
    return int(time.time())

# --- USER CAPS (tier-based) ---
USER_CAPS = {
    "FREE":  1e18,
    "PLUS":  1e18,
    "PRO":   1e18,
    "ENT":   1e18,
}
def _user_tier(user_id: Optional[str]) -> str:
    # Diserahkan ke API; router tidak enforce cap
    return os.getenv("DEFAULT_USER_TIER","FREE").upper()

def _user_cap_left(user_id: Optional[str]) -> float:
    tier = _user_tier(user_id)
    cap  = USER_CAPS.get(tier, USER_CAPS["FREE"])
    spent = budget_get_today_user(user_id)
    return max(0.0, cap - spent)

class UserCapExceeded(RuntimeError): ...

# ====== CACHE / BUDGET ======
_redis = None
if REDIS_URL:
    try:
        from redis import Redis
        _redis = Redis.from_url(REDIS_URL)
    except Exception:
        _redis = None

def cache_get(key: str) -> Optional[Dict[str, Any]]:
    if _redis:
        v = _redis.get(f"llm:cache:{key}")
        return json.loads(v) if v else None
    return None

def cache_set(key: str, val: Dict[str, Any], ttl: int = CACHE_TTL):
    if _redis:
        _redis.setex(f"llm:cache:{key}", ttl, json.dumps(val))

_budget_state: Dict[str, float] = {}
_provider_break = {
    "window_s": int(os.getenv("PROVIDER_BREAK_WINDOW_S","60")),
    "max_fails": int(os.getenv("PROVIDER_BREAK_FAILS","5")),
    "cooldown_s": int(os.getenv("PROVIDER_BREAK_COOLDOWN_S","90")),
}
_provider_state: Dict[str, Dict[str, Any]] = {}

def _cb_trip(provider: str) -> bool:
    st = _provider_state.setdefault(provider, {"fails":[], "until":0})
    now = _now_s()
    if now < st.get("until",0):
        return True
    st["fails"] = [t for t in st["fails"] if now - t <= _provider_break["window_s"]]
    return False

def _cb_record(provider: str, ok: bool):
    now = _now_s()
    st = _provider_state.setdefault(provider, {"fails":[], "until":0})
    if ok:
        st["fails"].clear()
        st["until"] = 0
    else:
        st["fails"].append(now)
        window = _provider_break["window_s"]
        maxf   = _provider_break["max_fails"]
        if len([t for t in st["fails"] if now - t <= window]) >= maxf:
            st["until"] = now + _provider_break["cooldown_s"]

def budget_inc_usd(delta: float) -> float:
    """increase today spend; return current total"""
    day = time.strftime("%Y-%m-%d")
    if _redis:
        k = f"llm:budget:{day}"
        try:
            cur = _redis.incrbyfloat(k, delta)
            _redis.expire(k, 86400)
            return float(cur)
        except Exception:
            pass
    _budget_state["total"] = _budget_state.get("total", 0.0) + delta
    return _budget_state["total"]

def budget_get_today() -> float:
    day = time.strftime("%Y-%m-%d")
    if _redis:
        v = _redis.get(f"llm:budget:{day}")
        return float(v) if v else 0.0
    return float(_budget_state.get("total", 0.0))

def _est_cost_usd(model, in_tok, out_tok):
    ipk = float(os.getenv("PRICE_IN_PER_1K", "0.002"))
    opk = float(os.getenv("PRICE_OUT_PER_1K","0.006"))
    return (in_tok/1000.0)*ipk + (out_tok/1000.0)*opk

def _normalize_router_result(prompt, raw):
    txt = ""
    if isinstance(raw, dict):
        txt = str(raw.get("text") or raw.get("output") or "")
        usage = raw.get("usage") or {}
        in_tok  = int(usage.get("in",  usage.get("prompt_tokens", 0)) or 0)
        out_tok = int(usage.get("out", usage.get("completion_tokens", 0)) or 0)
    else:
        usage = {}
        in_tok = out_tok = 0

    if in_tok == 0:
        in_tok = max(1, len(prompt)//4)
    if out_tok == 0:
        out_tok = max(1, len(txt)//4)

    usage = {
        "in": in_tok,
        "out": out_tok,
        "prompt_tokens": in_tok,
        "completion_tokens": out_tok,
    }

    cost = float(raw.get("cost_usd", 0.0)) if isinstance(raw, dict) else 0.0
    if cost == 0.0:
        cost = _est_cost_usd(str(raw.get("model","")), in_tok, out_tok)

    model = str(raw.get("model","")) if isinstance(raw, dict) else ""
    return {"text": txt, "model": model, "usage": usage, "cost_usd": cost}

def _normalize_prompt(p: str) -> str:
        if not isinstance(p, str):
            return ""
        s = unicodedata.normalize("NFC", p)
        s = s.replace("\r\n", "\n").replace("\r", "\n")
        s = re.sub(r"[ \t]+", " ", s)
        s = re.sub(r"\n{3,}", "\n\n", s)
        return s.strip()

# Wrap a provider call with breaker+log (use inside router send)
def _provider_call(fn, provider: str, *a, **k):
    if _cb_trip(provider):
        raise RuntimeError(f"provider_circuit_open:{provider}")
    try:
         res = fn(*a, **k)
         _cb_record(provider, True)
         return res
    except Exception as e:
        _cb_record(provider, False)
        raise

def budget_inc_usd_user(user_id: Optional[str], delta: float) -> float:
    if not user_id:
        return -1.0
    day = time.strftime("%Y-%m-%d")
    if _redis:
        k = f"llm:budget_user:{user_id}:{day}"
        cur = _redis.incrbyfloat(k, delta)
        _redis.expire(k, 86400)
        return float(cur)
    _budget_state[f"user_{user_id}_total"] = _budget_state.get(f"user_{user_id}_total", 0.0) + delta
    return _budget_state[f"user_{user_id}_total"]

def budget_get_today_user(user_id: Optional[str]) -> float:
    if not user_id:
        return 0.0
    day = time.strftime("%Y-%m-%d")
    if _redis:
        v = _redis.get(f"llm:budget_user:{user_id}:{day}")
        return float(v) if v else 0.0
    return float(_budget_state.get(f"user_{user_id}_total", 0.0))

# --- Provider circuit breaker ---
CB_ERR_LIMIT = int(os.getenv("LLM_CB_ERR_LIMIT", "5"))
CB_COOLDOWN_S = int(os.getenv("LLM_CB_COOLDOWN_S", "60"))

def _cb_key(prov: str, suffix: str): return f"llm:cb:{prov}:{suffix}"

def cb_allow(prov: str) -> bool:
    if not _redis or not prov:
        return True
    open_until = _redis.get(_cb_key(prov, "open_until"))
    return (not open_until) or (int(open_until) <= int(time.time()))

def cb_record_success(prov: str):
    if not _redis or not prov:
        return
    pipe = _redis.pipeline()
    pipe.delete(_cb_key(prov, "err"))
    pipe.delete(_cb_key(prov, "open_until"))
    pipe.execute()

def cb_record_error(prov: str):
    if not _redis or not prov:
        return
    err = int(_redis.incr(_cb_key(prov, "err")))
    _redis.expire(_cb_key(prov, "err"), CB_COOLDOWN_S)
    if err >= CB_ERR_LIMIT:
        _redis.setex(_cb_key(prov, "open_until"), CB_COOLDOWN_S, int(time.time()) + CB_COOLDOWN_S)

INFLIGHT_LIMIT = int(os.getenv("LLM_INFLIGHT_PER_USER", "3"))
RPM_LIMIT = int(os.getenv("LLM_RPM_PER_USER", "60"))

def inflight_allow(user_id: Optional[str]) -> bool:
    if not (_redis and user_id):
        return True
    try:
        cur = int(_redis.get(f"llm:inflight:{user_id}") or 0)
    except Exception:
        cur = 0
    return cur < INFLIGHT_LIMIT

def rpm_allow(user_id: Optional[str]) -> bool:
    if not (_redis and user_id):  # tanpa Redis: lewati (EC sudah gating)
        return True
    minute = int(time.time() // 60)
    k = f"llm:rpm:{user_id}:{minute}"
    v = int(_redis.incr(k))
    _redis.expire(k, 65)
    return v <= RPM_LIMIT

class InflightExceeded(RuntimeError): ...

def inflight_inc(user_id: Optional[str]):
    if not (_redis and user_id):
        return 0
    k = f"llm:inflight:{user_id}"
    v = int(_redis.incr(k))
    _redis.expire(k, 30)  # auto-clean 30s
    if v > INFLIGHT_LIMIT:
        _redis.decr(k)
        raise InflightExceeded(f"inflight>{INFLIGHT_LIMIT}")
    return v

def inflight_dec(user_id: Optional[str]):
    if not (_redis and user_id): return
    try:
        _redis.decr(f"llm:inflight:{user_id}")
    except Exception:
        pass

# ====== ROUTE ======
def _log_route(task_type: str, picked: str, modalities: Optional[set], need_ctx: int, user_id: Optional[str]):
    _log_jsonl(USAGE_LOG_PATH.replace("model_usage.jsonl","router_trace.jsonl"), {
        "ts": _now_s(), "user": user_id, "task": task_type,
        "modalities": sorted(list(modalities)) if modalities else [],
        "need_ctx": need_ctx, "model": picked
    })

def get_route(task_type: str = "default",
              modalities: Optional[set] = None,
              need_ctx: int = 8_000,
              user_id: Optional[str] = None) -> str:
    # 1) user override
    if user_id and user_id in _USER_MODEL_OVERRIDE:
        cand = _USER_MODEL_OVERRIDE[user_id]
        if _supports(modalities, cand) and MODEL_META.get(cand, {}).get("ctx", 0) >= need_ctx:
            _log_route(task_type, cand, modalities, need_ctx, user_id); return cand
    # 2) policy route-by-task
    cand = LLM_POLICY["route_by_task"].get(task_type, LLM_DEFAULT_MODEL)
    if _supports(modalities, cand) and MODEL_META.get(cand, {}).get("ctx", 0) >= need_ctx:
        _log_route(task_type, cand, modalities, need_ctx, user_id); return cand
    # 3) fallback list
    for m in LLM_POLICY["fallback_order"]:
        if _supports(modalities, m) and MODEL_META.get(m, {}).get("ctx", 0) >= need_ctx:
            _log_route(task_type, m, modalities, need_ctx, user_id); return m
    # 4) default
    _log_route(task_type, LLM_DEFAULT_MODEL, modalities, need_ctx, user_id)
    return LLM_DEFAULT_MODEL

def get_model_stats():
    return {"available": list(MODEL_META.keys()), "override_users": list(_USER_MODEL_OVERRIDE.keys())}

# ====== ADAPTERS (OpenAI / Anthropic) ======
def _openai_generate(model: str, prompt: str, **kw) -> Dict[str, Any]:
    from javu_agi.llm.openai_adapter import generate as openai_gen
    return openai_gen(prompt, model=model, **kw)

def _anthropic_generate(model: str, prompt: str, **kw) -> Dict[str, Any]:
    from javu_agi.llm.anthropic_adapter import generate as anth_gen
    return anth_gen(prompt, model=model, **kw)

def _call_provider(model: str, prompt: str, **kw) -> Dict[str, Any]:
    provider = MODEL_META.get(model, {}).get("provider")
    if provider == "openai":   return _openai_generate(model, prompt, **kw)
    if provider == "anthropic":return _anthropic_generate(model, prompt, **kw)
    # fallback asumsi OpenAI
    return _openai_generate(model, prompt, **kw)

def _local_generate(model: str, prompt: str, **kw) -> dict:
    """
    Load pipeline dari ckpt_dir yang teregistrasi paling baru.
    NOTE: di produksi: pakai server model (vLLM/text-generation-inference) & panggil via HTTP.
    Di dev: kita load transformers langsung (cukup untuk bukti).
    """
    # pick latest from LOCAL_REG
    if not LOCAL_REG: 
        return {"text":"[LOCAL_MODEL_NONE]"}
    ckpt = sorted(LOCAL_REG, key=lambda x: x.get("registered_at",0))[-1]["ckpt_dir"]
    try:
        from transformers import AutoTokenizer, AutoModelForCausalLM
        tok = AutoTokenizer.from_pretrained(ckpt, use_fast=True)
        mdl = AutoModelForCausalLM.from_pretrained(ckpt)
        import torch
        dev = "cuda" if torch.cuda.is_available() else "cpu"
        mdl = mdl.to(dev)
        ipt = tok(prompt, return_tensors="pt").to(dev)
        out = mdl.generate(**ipt, max_new_tokens=kw.get("max_tokens",512), temperature=kw.get("temperature",0.2))
        txt = tok.decode(out[0], skip_special_tokens=True)
        if txt.startswith(prompt): txt = txt[len(prompt):]
        return {"text": txt.strip()}
    except Exception as e:
        return {"text": f"[LOCAL_MODEL_ERROR] {e}"}

def _ensure_dir(p):
    pathlib.Path(p).mkdir(parents=True, exist_ok=True)

def _openai_image_generate(prompt: str, size: str = "1024x1024") -> str:
    h = hashlib.sha1(f"{size}|{prompt}".encode("utf-8")).hexdigest()
    _ensure_dir(IMG_CACHE_DIR)
    out = os.path.join(IMG_CACHE_DIR, f"{h}.png")

    # budget precheck
    try:
        budget_precheck("openai_image", min_left=0.02)
    except BudgetExceeded:
        return text_image_stub(prompt, size=size)

    # cache hit
    if os.path.exists(out):
        try:
            budget_consume("openai_image", 0.02)
        except Exception:
            pass
        return out

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return text_image_stub(prompt, size=size)

    url = "https://api.openai.com/v1/images/generations"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type":"application/json"}
    payload = {"model":"dall-e-3", "prompt": prompt, "size": size}
    r = requests.post(url, headers=headers, json=payload, timeout=120)
    r.raise_for_status()
    data = r.json()
    img_url = data["data"][0]["url"]

    # download
    try:
        binr = requests.get(img_url, timeout=120).content
        with open(out, "wb") as f:
            f.write(binr)
        try:
            budget_consume("openai_image", 0.02)
        except Exception:
            pass
        return out
    except Exception:
        return img_url

def _elevenlabs_tts(text: str) -> str:
    _ensure_dir(TTS_CACHE_DIR)
    h = hashlib.sha1(text.encode("utf-8")).hexdigest()
    out = os.path.join(TTS_CACHE_DIR, f"{h}.mp3")

    if os.path.exists(out):
        return out

    # budget precheck
    try:
        budget_precheck("elevenlabs", min_left=0.01)
    except BudgetExceeded:
        return subtitles_from_text(text)

    key = os.getenv("ELEVENLABS_API_KEY")
    if not key:
        return subtitles_from_text(text)

    voice = ELEVEN_VOICE_ID
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice}?optimize_streaming_latency=0"
    hdr = {"xi-api-key": key, "accept": "audio/mpeg", "Content-Type":"application/json"}
    payload = {"text": text, "voice_settings": {"stability": 0.4, "similarity_boost": 0.9}}

    r = requests.post(url, headers=hdr, json=payload, timeout=120)
    r.raise_for_status()

    with open(out, "wb") as f:
        f.write(r.content)
    try:
        budget_consume("elevenlabs", 0.01)
    except Exception:
        pass
    return out

def generate_with_model(model: str, prompt: str, **kw) -> Dict[str, Any]:
    """Paksa satu model tertentu, mengembalikan dict {text,...} untuk text; string path/url untuk media."""
    prov = MODEL_META.get(model, {}).get("provider")
    if prov == "openai":
        return _openai_generate(model, prompt, **kw)
    if prov == "anthropic":
        return _anthropic_generate(model, prompt, **kw)
    if prov == "openai_image":
        return {"text": "", "media": _openai_image_generate(prompt, size=kw.get("size","1024x1024"))}
    if prov == "elevenlabs":
        return {"text": "", "media": _elevenlabs_tts(prompt)}
    if prov == "local_video":
        return {"text":"", "media": _storyboard_to_video(kw.get("narration", prompt), base_prompt=prompt)}
    # default: route
    return route_and_generate(prompt, **kw)

def call_model(model: str, prompt: str) -> Any:
    """Wrapper sederhana: untuk text return string, untuk media return path/url."""
    out = generate_with_model(model, prompt, max_tokens=1024, temperature=0.2)
    if isinstance(out, dict):
        if "media" in out:
            return out["media"]
        return out.get("text","")
    return out

# ====== MAIN ENTRYPOINT: route + cache + budget + retry ======
def route_and_generate(prompt: str,
                       task_type: str = "default",
                       modalities: Optional[set] = None,
                       need_ctx: int = 8_000,
                       user_id: Optional[str] = None,
                       max_tokens: int = 1024,
                       temperature: float = 0.2,
                       tools: Optional[List[Dict[str, Any]]] = None,
                       system: Optional[str] = None,
                       distill_log: bool = False) -> Dict[str, Any]:
    """
    Kembalikan:
      {"text": ..., "model": ..., "usage": {"in": int, "out": int}, "cost_usd": float, "cached": bool}
    """
    prompt = _normalize_prompt(prompt)
    if os.getenv("KILL_SWITCH", "0").lower() in {"1","true","yes"}:
        return _normalize_router_result(prompt, {
            "text": "(router disabled by kill-switch)",
            "model": get_route(task_type, modalities, need_ctx, user_id),
            "usage": {"in": 0, "out": 0},
            "cost_usd": 0.0,
            "cached": False
        })
    
    # ---- cache key (+ early return jika hit) ----
    cache_key = _hash_payload({
        "p": prompt,
        "task": task_type,
        "mods": sorted(list(modalities)) if modalities else [],
        "ctx": need_ctx,
        "mx": max_tokens,
        "temp": temperature,
        "tools": tools,
        "sys": system,
        "uid": user_id,  # ← isolasi cache
    })
    
    cached = cache_get(cache_key)
    if cached:
        return {**_normalize_router_result(prompt, cached), "cached": True}
    
    # ---- per-user RPM guard (router-level) ----
    if not rpm_allow(user_id):
        return _normalize_router_result(prompt, {
            "text": "(limit tercapai untuk plan Anda hari ini)",
            "model": get_route(task_type, modalities, need_ctx, user_id),
            "usage": {"in": 0, "out": 0},
            "cost_usd": 0.0,
            "cached": False
        })

    if not inflight_allow(user_id):
        return _normalize_router_result(prompt, {
            "text": "(terlalu banyak request bersamaan, coba lagi nanti)",
            "model": get_route(task_type, modalities, need_ctx, user_id),
            "usage": {"in": 0, "out": 0},
            "cost_usd": 0.0,
            "cached": False
        })

    # ---- routing ----
    picked = get_route(task_type, modalities, need_ctx, user_id)

    # ---- kandidat + filter provider over-cap + circuit breaker ----
    providers_try = [picked] + [m for m in LLM_POLICY["fallback_order"] if m != picked]
    providers_try = [m for m in providers_try if not _provider_overcap(m)] or [picked]
    providers_try = [m for m in providers_try if cb_allow(MODEL_META.get(m, {}).get("provider",""))] or [picked]

    err_last = None
    for model in providers_try:
        prov = MODEL_META.get(model, {}).get("provider")
        try:
            # ---- user budget precheck (TEXT) ----
            left = _user_cap_left(user_id)
            # kira biaya worst-case kasar untuk precheck
            est_in  = max(1, len(prompt)//4)
            est_out = max_tokens
            est_cost = _est_cost_usd(model, est_in, est_out)
            if left < (0.5 * est_cost):
                if HIDE_CAP_ERRORS:
                    return _normalize_router_result(prompt, {
                        "text": "(limit tercapai untuk plan Anda hari ini)",
                        "model": model,
                        "usage": {"in": 0, "out": 0},
                        "cost_usd": 0.0,
                        "cached": False
                    })
                else:
                    raise UserCapExceeded(f"user daily cap reached; left=${left:.3f}")

            # ---- in-flight guard per user ----
            inflight_inc(user_id)

            # ---- panggil provider ----
            out = _call_provider(model, prompt,
                                 max_tokens=max_tokens, temperature=temperature,
                                 tools=tools, system=system)

            # ---- usage & cost ----
            usage   = out.get("usage") or {}
            in_tok  = int(usage.get("in",  usage.get("prompt_tokens", 0)))
            out_tok = int(usage.get("out", usage.get("completion_tokens", 0)))
            cost    = _est_cost_usd(model, in_tok, out_tok)

            # ---- akuntansi ----
            total_global = budget_inc_usd(cost)
            try: total_user = budget_inc_usd_user(user_id, cost)
            except Exception: total_user = None
            try:
                if prov in {"openai","anthropic","openai_image","elevenlabs","local_video"}:
                    provider_spend_inc(prov, cost)
            except Exception:
                pass
            
            # ---- normalize + fallback usage ----
            txt = (out.get("text") or out.get("output") or "") if isinstance(out, dict) else ""
            usage = out.get("usage") or {}
            in_tok  = int(usage.get("in",  usage.get("prompt_tokens", 0)) or 0)
            out_tok = int(usage.get("out", usage.get("completion_tokens", 0)) or 0)

            # Fallback kasar jika adapter tidak isi usage
            if in_tok == 0:
                in_tok = max(1, len(prompt) // 4)
            if out_tok == 0:
                out_tok = max(1, len(txt) // 4)
            usage = {"in": in_tok, "out": out_tok}
            cost  = _est_cost_usd(model, in_tok, out_tok)

            result = {
                "text": out.get("text") or out.get("output") or "",
                "model": model,
                "usage": {"in": in_tok, "out": out_tok},
                "cost_usd": cost
            }

            # ---- cache ----
            cache_set(cache_key, result, CACHE_TTL)

            # ---- optional: raw router distill log ----
            if distill_log or ROUTER_DISTILL_LOG:
                try:
                    os.makedirs(DISTILL_DIR, exist_ok=True)
                    with open(os.path.join(DISTILL_DIR, f"{int(time.time()*1000)}.json"), "w", encoding="utf-8") as f:
                        json.dump({
                            "prompt": prompt, "model": model,
                            "output": result["text"], "usage": result["usage"],
                            "cost": cost
                        }, f, ensure_ascii=False)
                except Exception:
                    pass

            # ---- router usage trace ----
            _log_jsonl(USAGE_LOG_PATH, {
                "ts": _now_s(), "user": user_id, "task": task_type, "model": model,
                "cost_usd": cost, "usage": result["usage"],
                "budget_today_global": total_global,
                **({"budget_today_user": total_user} if total_user is not None else {})
            })

            cb_record_success(prov)
            return {**result, "cached": False}

        except InflightExceeded:
            err_last = "inflight_limit"
            continue
        except UserCapExceeded as e:
            err_last = str(e)
            break
        except Exception as e:
            err_last = str(e)
            cb_record_error(prov)
            time.sleep(0.2)
            continue
        finally:
            inflight_dec(user_id)

    # ---- total failure ----
    _log_jsonl(USAGE_LOG_PATH, {"ts": _now_s(), "user": user_id, "task": task_type, "error": err_last, "picked": picked})
    return _normalize_router_result(prompt, {
        "text": "(router failure; try later)",
        "model": picked,
        "usage": {"in": 0, "out": 0},
        "cost_usd": 0.0,
        "cached": False
    })

def run_multimodal_task(task: str) -> dict:
    """
    Reasoning GPT-5 + Claude → merge → image (DALL·E 3) → audio (ElevenLabs) → video (storyboard).
    """
    out, err = {}, []

    # 1) reasoning (berurutan cepat; bisa parallel di masa depan)
    try:
        out["gpt"] = call_model("gpt-5", task)
    except Exception as e:
        err.append(f"gpt-5: {e}")
    try:
        out["claude"] = call_model("claude-opus-3", task)
    except Exception as e:
        err.append(f"claude-opus-3: {e}")

    # 2) merge
    merged = f"[GPT]\n{out.get('gpt','')}\n\n[Claude]\n{out.get('claude','')}".strip()
    out["merged_reasoning"] = merged

    # 3) image + audio
    try:
        out["image"] = call_model("dall-e-3", f"Cinematic keyframe for: {merged[:1600]}")
    except Exception as e:
        err.append(f"image: {e}")
    try:
        out["audio"] = call_model("elevenlabs-tts", f"Narration (concise, natural): {merged[:1600]}")
    except Exception as e:
        err.append(f"audio: {e}")

    # 4) video (storyboard)
    try:
        out["video"] = generate_with_model("storyboard-video", f"Cinematic storyboard for: {task}", narration=merged).get("media")
    except Exception as e:
        err.append(f"video: {e}")

    if err:
        out["errors"] = err
    return out

def _storyboard_to_video(narration_text: str, base_prompt: str) -> str:
    _ensure_dir(VIDEO_OUT_DIR)

    # budget precheck
    try:
        budget_precheck("local_video", min_left=0.05)
    except BudgetExceeded:
        return text_slideshow_video(narration_text, frames=VIDEO_FRAMES, fps=VIDEO_FPS, size=VIDEO_SIZE)

    # pecah narasi → scene
    chunks = [s.strip() for s in narration_text.split(".") if s.strip()] or [narration_text[:200]]
    scene_prompts = [f"{base_prompt}. Scene {i+1}: {chunks[i % len(chunks)]}" for i in range(VIDEO_FRAMES)]

    # generate frames
    frame_paths = []
    for sp in scene_prompts:
        fp = _openai_image_generate(sp, size=VIDEO_SIZE)
        frame_paths.append(fp)

    # stitch
    ts = hashlib.sha1(("|".join(frame_paths)).encode("utf-8")).hexdigest()
    frames_list = os.path.join(VIDEO_OUT_DIR, f"{ts}.txt")
    with open(frames_list, "w", encoding="utf-8") as f:
        for fp in frame_paths:
            f.write(f"file '{os.path.abspath(fp)}'\n")

    raw_mp4 = os.path.join(VIDEO_OUT_DIR, f"{ts}_raw.mp4")
    final_mp4 = os.path.join(VIDEO_OUT_DIR, f"{ts}.mp4")

    subprocess.run(["ffmpeg","-y","-f","concat","-safe","0","-i",frames_list,
                    "-r", str(VIDEO_FPS), "-pix_fmt","yuv420p", raw_mp4], check=True)

    # audio narasi
    audio_path = _elevenlabs_tts(narration_text)

    subprocess.run(["ffmpeg","-y","-i", raw_mp4, "-i", audio_path,
                    "-c:v","copy","-c:a","aac","-shortest", final_mp4], check=True)
    try:
        budget_consume("local_video", 0.05)
    except Exception:
        pass
    return final_mp4

def generate_image_any(prompt: str, size: str = "1024x1024") -> str:
    try:
        return _openai_image_generate(prompt, size=size)
    except Exception:
        return text_image_stub(prompt, size=size)

def generate_video_any(narration: str, base_prompt: str) -> str:
    try:
        return _storyboard_to_video(narration, base_prompt=base_prompt)
    except Exception:
        return text_slideshow_video(narration, frames=VIDEO_FRAMES, fps=VIDEO_FPS, size=VIDEO_SIZE)

# === Adapter so ExecutiveController() can instantiate ===
class LLMRouter:
    def __init__(self, default_task: str = "default"):
        self.default_task = default_task

    def call(self,
             prompt: str,
             *,
             user_id: Optional[str] = None,
             task_type: Optional[str] = None,
             modalities: Optional[set] = None,
             need_ctx: int = 8_000,
             max_tokens: int = 1024,
             temperature: float = 0.2,
             tools: Optional[List[Dict[str, Any]]] = None,
             system: Optional[str] = None,
             distill_log: bool = False) -> Dict[str, Any]:

        res = route_and_generate(prompt,
                                 task_type=task_type or self.default_task,
                                 modalities=modalities,
                                 need_ctx=need_ctx,
                                 user_id=user_id,
                                 max_tokens=max_tokens,
                                 temperature=temperature,
                                 tools=tools,
                                 system=system,
                                 distill_log=distill_log)

        # normalisasi usage agar konsisten
        u = dict(res.get("usage") or {})
        u.setdefault("prompt_tokens", int(u.get("in", 0)))
        u.setdefault("completion_tokens", int(u.get("out", 0)))
        u.setdefault("in", int(u.get("prompt_tokens", 0)))
        u.setdefault("out", int(u.get("completion_tokens", 0)))
        res["usage"] = u

        try:
            res["cost_usd"] = float(res.get("cost_usd", 0.0))
        except Exception:
            res["cost_usd"] = 0.0

        return res

def post_refine(text: str, constitution: list[str], guidance: str) -> str:
    if not text:
        return text
    head = " ".join(constitution[:3])
    return f"{text.strip()}\n\n— {guidance}\n— Prinsip: {head}"

def _local_generate(model: str, prompt: str, **kw) -> dict:
    raise RuntimeError("local model loading disabled (vendor-only mode)")

_orig_route_and_generate = route_and_generate
def route_and_generate(*a, **kw):
    kw.pop("distill_log", None)
    return _orig_route_and_generate(*a, distill_log=False, **kw)

