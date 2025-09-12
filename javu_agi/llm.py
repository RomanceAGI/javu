from typing import Tuple
import time, math
# Import configuration from the local package.  Using an absolute import avoids shadowing
# the external ``config`` package when this module is executed outside the package context.
from javu_agi.config import (
    MAX_TOKENS_PER_CALL,
    DEFAULT_RETRY,
    export_router_context,
    get_model_config,
)
from javu_agi.llm_router import get_route
from javu_agi.memory.memory import recall_from_memory
from javu_agi.budget_guard import estimate_tokens_from_text, track_usage
from javu_agi.model_usage import estimate_cost_usd

_openai = None
_anthropic = None
_elevenlabs = None

# Mapping of high-level role descriptors to task types used by the LLM router.
# If a role is not found in this mapping the default task type is used.
ROLE_TO_TASK: dict[str, str] = {
    "General": "default",
    "Planner": "plan",
    "Programmer": "code",
    "Researcher": "search",
    "Designer": "video",
}


def _ensure_openai():
    global _openai
    if _openai is None:
        from openai import OpenAI

        _openai = OpenAI()
    return _openai


def _ensure_anthropic():
    global _anthropic
    if _anthropic is None:
        import anthropic

        _anthropic = anthropic.Anthropic()
    return _anthropic


def _ensure_elevenlabs():
    global _elevenlabs
    if _elevenlabs is None:
        import elevenlabs

        _elevenlabs = elevenlabs.elevenlabs()
    return _elevenlabs


def _call_openai_chat(model: str, sys: str, usr: str, temp: float, maxtok: int):
    cli = _ensure_openai()
    resp = cli.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": sys or "You are a powerful reasoning model. Be precise.",
            },
            {"role": "user", "content": usr},
        ],
        temperature=temp,
        max_tokens=maxtok,
    )
    out = resp.choices[0].message.content
    usage = getattr(resp, "usage", None)
    pt = getattr(usage, "prompt_tokens", None)
    ct = getattr(usage, "completion_tokens", None)
    return out, pt, ct


def _call_anthropic_chat(model: str, sys: str, usr: str, temp: float, maxtok: int):
    cli = _ensure_anthropic()
    resp = cli.messages.create(
        model=model,
        system=sys or "You are a powerful reasoning model. Be precise.",
        max_tokens=maxtok,
        temperature=temp,
        messages=[{"role": "user", "content": [{"type": "text", "text": usr}]}],
    )
    out = "".join(
        [blk.text for blk in resp.content if getattr(blk, "type", "") == "text"]
    )
    pt = getattr(resp, "usage", {}).get("input_tokens")
    ct = getattr(resp, "usage", {}).get("output_tokens")
    return out, pt, ct


def _exec_with_provider(
    model: str, sys: str, usr: str, temp: float, maxtok: int
) -> Tuple[str, int, int]:
    cfg = get_model_config(model)
    prov = (cfg or {}).get("provider", "openai")
    if prov == "anthropic":
        return _call_anthropic_chat(model, sys, usr, temp, maxtok)
    return _call_openai_chat(model, sys, usr, temp, maxtok)


def _retry_loop(
    models: list, sys: str, usr: str, temp: float, maxtok: int
) -> Tuple[str, str]:
    maxr = DEFAULT_RETRY.get("max_retries", 3)
    back = DEFAULT_RETRY.get("backoff_s", 1.5)
    last_err = ""
    for attempt in range(maxr):
        m = models[min(attempt, len(models) - 1)]
        try:
            out, pt, ct = _exec_with_provider(m, sys, usr, temp, maxtok)
            return out, m
        except Exception as e:
            last_err = str(e)
            time.sleep(back * (1.5**attempt))
    raise RuntimeError(last_err or "llm_failed")


def call_llm(
    prompt: str,
    system_prompt: str = "",
    temperature: float = 0.7,
    task_type: str = "default",
    modalities: set | None = None,
    max_tokens: int | None = None,
    user_id: str | None = None,
) -> str:
    temperature = float(max(0.0, min(1.0, temperature)))
    need_ctx = min(MAX_TOKENS_PER_CALL, (max_tokens or 8000))
    primary = get_route(
        task_type=task_type, modalities=modalities, need_ctx=need_ctx, user_id=user_id
    )
    ctx = export_router_context()
    chain = [primary] + [m for m in ctx["policy"]["fallback_order"] if m != primary]
    # Estimasi biaya (tanpa gate harian/global)
    prompt_tokens_est = estimate_tokens_from_text((system_prompt or "") + "\n" + prompt)
    completion_tokens_est = min(need_ctx, max(256, need_ctx // 2))
    # eksekusi
    try:
        out, model_used = _retry_loop(
            chain, system_prompt, prompt, temperature, need_ctx
        )
        used_prompt_toks = prompt_tokens_est
        used_completion_toks = estimate_tokens_from_text(out or "")
        spent = estimate_cost_usd(model_used, used_prompt_toks, used_completion_toks)
        track_usage(
            model_used,
            used_prompt_toks,
            used_completion_toks,
            spent,
            user_id=user_id or "system",
        )
        try:
            import sqlite3, os, datetime

            db = os.getenv("BUDGET_SQLITE_PATH", "/data/budget.db")
            day = datetime.date.today().isoformat()
            con = sqlite3.connect(db, timeout=2.0)
            con.execute(
                """
                        CREATE TABLE IF NOT EXISTS user_budget_daily(
                        user_id TEXT, day TEXT, spent_usd REAL NOT NULL DEFAULT 0,
                        PRIMARY KEY(user_id, day)
                        )
                        """
            )
            con.execute(
                """
                        INSERT INTO user_budget_daily(user_id, day, spent_usd) VALUES (?,?,?)
                        ON CONFLICT(user_id, day) DO UPDATE SET spent_usd = spent_usd + excluded.spent_usd
            """,
                (user_id or "system", day, float(spent)),
            )
            con.commit()
            con.close()
        except Exception:
            pass
        return out
    except Exception as e:
        return f"[LLM ERROR] {str(e)}"


def ask_llm(prompt: str, role: str = "General", user_id: str = "user-001") -> str:
    """
    Generate a response from the language model given a user prompt and role.

    This helper will automatically look up the task type based on the high level role
    (e.g. Planner, Programmer) and assemble a system prompt that injects recalled
    context from memory for the given user. It then delegates to ``call_llm``.

    Parameters
    ----------
    prompt : str
        The user query for the model.
    role : str, optional
        A high‑level role descriptor (default is ``"General"``).
    user_id : str, optional
        The id of the user making the request (default is ``"user-001"``).

    Returns
    -------
    str
        The model's response text.
    """
    # Recall relevant context for this user and prompt to prime the model.
    recalled_context = recall_from_memory(user_id, prompt, top_k=3) if user_id else ""
    # Construct a system prompt in Indonesian instructing the model about its role
    # and injecting any recalled context.
    system_prompt = f"""
Kamu adalah {role} JAVU, AGI digital autonomy yang cerdas, etis dan profesional.

Gunakan konteks masa lalu jika relevan:
{recalled_context}
""".strip()
    # Map the role to a known task type; fall back to default when unknown.
    task_type = ROLE_TO_TASK.get(role, "default")
    # Delegate to the core LLM invocation.
    return call_llm(
        prompt=prompt,
        system_prompt=system_prompt,
        task_type=task_type,
        user_id=user_id,
    )
