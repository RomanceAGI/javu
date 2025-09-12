from __future__ import annotations
import os, json, yaml
# ``dotenv`` is optional; define a no-op fallback if missing.  This allows
# importing the configuration module without having python-dotenv installed.
try:
    from dotenv import load_dotenv  # type: ignore
except Exception:
    def load_dotenv(*_args, **_kwargs):  # type: ignore
        """Fallback ``load_dotenv`` that does nothing when dotenv is unavailable."""
        return False

load_dotenv()

# === API Keys ===
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY") or os.getenv("LLM_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# === Provider Registry ===
# Catatan:
# - model name → provider ditentukan via prefix map & override MODELS_CONFIG.
# - Bisa di-extend (Google, Mistral, Cohere) tanpa ubah kode.
PROVIDERS = {
    "openai": {
        "api_key_env": "OPENAI_API_KEY",
        "default_timeout_s": float(os.getenv("OPENAI_TIMEOUT_S", "60")),
        "ratelimit_rps": float(os.getenv("OPENAI_RPS", "2.0")),
        "max_tokens_per_call": int(os.getenv("OPENAI_MAX_TOKENS", "8192")),
        "models": {
            # isi default; bisa override lewat MODELS_CONFIG
            "gpt-5": {"family": "text", "vision": False},
            "gpt-5-mini": {"family": "text", "vision": False},
            "gpt-5-nano": {"family": "text", "vision": False},
            "gpt-4o": {"family": "text", "vision": True},
            "gpt-image-1": {"family": "image", "vision": False},
        },
    },
    "anthropic": {
        "api_key_env": "ANTHROPIC_API_KEY",
        "default_timeout_s": float(os.getenv("ANTHROPIC_TIMEOUT_S", "60")),
        "ratelimit_rps": float(os.getenv("ANTHROPIC_RPS", "1.5")),
        "max_tokens_per_call": int(os.getenv("ANTHROPIC_MAX_TOKENS", "8192")),
        "models": {
            # Nama umum → Claude varian (ubah via MODELS_CONFIG kalau perlu)
            "claude-3-opus": {"family": "text", "vision": True},
            "claude-3-sonnet": {"family": "text", "vision": True},
            "claude-3-haiku": {"family": "text", "vision": True},
            "claude-3-5-sonnet": {"family": "text", "vision": True},
        },
    },
}

# === Default Text LLM ===
LLM_DEFAULT_MODEL = os.getenv("LLM_DEFAULT_MODEL", "gpt-5")

# === Routing Kebijakan Model (task → model) ===
# Tambah rute ke Claude untuk task "reason" default.
LLM_POLICY = {
    "route_by_task": {
        "plan": os.getenv("ROUTE_PLAN", "gpt-5"),
        "reason": os.getenv("ROUTE_REASON", "claude-3-opus"),
        "analyze": os.getenv("ROUTE_ANALYZE", "gpt-5"),
        "reflect": os.getenv("ROUTE_REFLECT", "claude-3-sonnet"),
        "code": os.getenv("ROUTE_CODE", "gpt-5"),
        "tool": os.getenv("ROUTE_TOOL", "gpt-4o"),
        "web": os.getenv("ROUTE_WEB", "gpt-5-mini"),
        "action": os.getenv("ROUTE_ACTION", "gpt-5-mini"),
        "vision": os.getenv("ROUTE_VISION", "gpt-4o"),
        "fast": os.getenv("ROUTE_FAST", "gpt-5-nano"),
        "default": os.getenv("ROUTE_DEFAULT", "gpt-5"),
    },
    "fallback_order": [
        m.strip()
        for m in os.getenv(
            "ROUTE_FALLBACK_ORDER",
            "gpt-5, claude-3-sonnet, gpt-4o, gpt-5-mini, claude-3-haiku",
        ).split(",")
    ],
    # Kebijakan budget per task (opsional)
    "task_caps_usd": {
        "plan": float(os.getenv("CAP_PLAN_USD", "2.5")),
        "reason": float(os.getenv("CAP_REASON_USD", "3.0")),
        "analyze": float(os.getenv("CAP_ANALYZE_USD", "1.5")),
        "code": float(os.getenv("CAP_CODE_USD", "2.0")),
        "default": float(os.getenv("CAP_DEFAULT_USD", "1.0")),
    },
}

# === Image Gen Model ===
IMAGE_MODEL = os.getenv("IMAGE_MODEL", "gpt-image-1")  # bisa diganti "dall-e-3"

# === Audio/STT/TTS (opsional) ===
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
TTS_VOICE_ID = os.getenv("TTS_VOICE_ID", "EXAVITQu4vr4xnSDxMaL")
STT_MODEL = os.getenv("STT_MODEL", "whisper-1")

# === Budget & Router Telemetry ===
BUDGET_DAILY_USD = float(os.getenv("BUDGET_DAILY_USD", "50"))
MAX_TOKENS_PER_CALL = int(os.getenv("MAX_TOKENS_PER_CALL", "8192"))
ROUTER_LOGGING_ENABLED = os.getenv("ROUTER_LOGGING_ENABLED", "true").lower() == "true"
USAGE_LOG_PATH = os.getenv("USAGE_LOG_PATH", "logs/model_usage.jsonl")


# === File Policies ===
def _yload(p: str):
    with open(p, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


POLICY_FILE = os.getenv("POLICY_FILE", "/opt/agi/safety/policy.yaml")
PERMISSIONS_FILE = os.getenv("PERMISSIONS_FILE", "javu_agi/tools/permission.yaml")
MODELS_CONFIG = os.getenv("MODELS_CONFIG", "/opt/agi/config/models.yaml")
ROUTER_POLICY = os.getenv("ROUTER_POLICY", "/opt/agi/config/router_policy.yaml")


def load_policy():
    return _yload(POLICY_FILE)


def load_permissions():
    return _yload(PERMISSIONS_FILE)


def load_models_cfg():
    return _yload(MODELS_CONFIG)


def load_router_policy():
    return _yload(ROUTER_POLICY)


# === Retry / Timeout Default ===
DEFAULT_RETRY = {
    "max_retries": int(os.getenv("LLM_MAX_RETRIES", "3")),
    "backoff_s": float(os.getenv("LLM_BACKOFF_S", "1.5")),
    "timeout_s": float(os.getenv("LLM_TIMEOUT_S", "60")),
}


# === Model Resolver ===
# Menentukan provider dari nama model & gabungkan konfigurasi (MODELS_CONFIG kalau ada)
def _provider_for_model(model: str) -> str:
    m = (model or "").lower()
    if m.startswith("gpt-"):
        return "openai"
    if m.startswith("claude-"):
        return "anthropic"
    # fallback: cek registry eksternal
    try:
        cfg = load_models_cfg()  # {provider: {models: {...}}}
        for prov, meta in (cfg or {}).items():
            if "models" in meta and model in meta["models"]:
                return prov
    except Exception:
        pass
    return "openai"  # default


def get_model_config(model: str) -> dict:
    prov = _provider_for_model(model)
    base = (PROVIDERS.get(prov) or {}).copy()
    model_meta = (base.get("models") or {}).get(model, {})
    # overlay dari MODELS_CONFIG
    try:
        ext = load_models_cfg()  # {provider: {models: {model: {...}}}}
        if (
            ext
            and prov in ext
            and "models" in ext[prov]
            and model in ext[prov]["models"]
        ):
            model_meta = {**model_meta, **ext[prov]["models"][model]}
    except Exception:
        pass
    return {
        "provider": prov,
        "api_key": os.getenv(base.get("api_key_env", "")),
        "timeout_s": base.get("default_timeout_s", DEFAULT_RETRY["timeout_s"]),
        "ratelimit_rps": base.get("ratelimit_rps", 1.0),
        "max_tokens_per_call": base.get("max_tokens_per_call", MAX_TOKENS_PER_CALL),
        "model_meta": model_meta,
    }


def resolve_model_for_task(task: str) -> str:
    route = LLM_POLICY["route_by_task"]
    return route.get(task, route["default"])


def provider_for_task(task: str) -> dict:
    model = resolve_model_for_task(task)
    return get_model_config(model)


# === Sanity: minimal guard jika key hilang ===
def assert_keys():
    miss = []
    # Wajib minimal salah satu provider ada
    if not OPENAI_API_KEY and not ANTHROPIC_API_KEY:
        miss.append("OPENAI_API_KEY_or_ANTHROPIC_API_KEY")
    # Vision routing butuh model vision-enabled
    if (
        LLM_POLICY["route_by_task"].get("vision", "gpt-4o").startswith("claude")
        and not ANTHROPIC_API_KEY
    ):
        miss.append("ANTHROPIC_API_KEY_for_vision_route")
    return miss


# === Convenience for clients (router) ===
def export_router_context() -> dict:
    return {
        "default_model": LLM_DEFAULT_MODEL,
        "policy": LLM_POLICY,
        "budget_daily_usd": BUDGET_DAILY_USD,
        "retry": DEFAULT_RETRY,
        "providers": {
            "openai": {"enabled": bool(OPENAI_API_KEY)},
            "anthropic": {"enabled": bool(ANTHROPIC_API_KEY)},
        },
    }
