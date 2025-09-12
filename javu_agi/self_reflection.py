from javu_agi.llm import call_llm
from javu_agi.memory.memory import save_to_memory
from javu_agi.utils.logger import log


def reflect_on_conversation(user_id, history: list[str]):
    if not history:
        return "[REFLECTION] Tidak ada histori."

    joined = "\n".join(history[-5:])
    prompt = f"""
Kamu adalah AI yang sedang merenung.

Apa insight dari interaksi ini:
{joined}

Jawab singkat.
"""
    reflection = call_llm(prompt).strip()
    save_to_memory(user_id, f"[REFLECTION] {reflection}")
    log_user(user_id, f"[REFLECTION] {reflection}")
    return reflection


def reflect_outcome(user_id: str, goal: str, outcome_text: str, meta: dict):
    """
    Refleksi berbasis outcome & meta (verifier/halluc/tokens), tetap simpan ke memory.
    Return: dict {"score": float, "hint": str, "ts": iso}
    """
    # Bound & sanitasi
    sample = (outcome_text or "")[:4000]
    joined_meta = {
        "verifier": float((meta or {}).get("verifier", {}).get("score", 0.0)),
        "hallucination_rate": float((meta or {}).get("hallucination_rate", 0.0)),
        "tokens_prompt": int((meta or {}).get("tokens_prompt", 0)),
        "tokens_output": int((meta or {}).get("tokens_output", 0)),
        "repaired": bool((meta or {}).get("repaired", False)),
    }

    prompt = f"""Kamu adalah AI yang sedang melakukan self-reflection.
Tugas: nilai kualitas hasil dan berikan saran perbaikan singkat.
Goal: {goal}

HASIL (dipotong): 
{sample}

META:
- verifier: {joined_meta["verifier"]}
- hallucination_rate: {joined_meta["hallucination_rate"]}
- tokens_prompt: {joined_meta["tokens_prompt"]}
- tokens_output: {joined_meta["tokens_output"]}
- repaired: {joined_meta["repaired"]}

Outputkan JSON dgn keys: score (0..1), hint (<=120 char).
"""
    try:
        raw = call_llm(prompt).strip()
    except Exception as e:
        raw = f'{{"score": 0.0, "hint": "LLM error: {str(e)[:80]}"}}'

    # Parsing aman
    try:
        import json as _json, datetime as _dt

        obj = (
            _json.loads(raw)
            if raw.startswith("{")
            else {"score": 0.0, "hint": raw[:120]}
        )
        obj["score"] = float(obj.get("score", 0.0))
        obj["hint"] = str(obj.get("hint", ""))[:200]
        obj["ts"] = _dt.datetime.utcnow().isoformat()
    except Exception:
        from datetime import datetime as _dt

        obj = {"score": 0.0, "hint": raw[:200], "ts": _dt.utcnow().isoformat()}

    # Persist ke memory + log (pakai 'log' yang sudah di-import)
    try:
        save_to_memory(
            user_id,
            f"[REFLECTION] goal={goal} score={obj['score']:.3f} hint={obj['hint']}",
        )
    except Exception:
        pass
    try:
        log(user_id, f"[REFLECTION] {obj}")
    except Exception:
        pass
    return obj
