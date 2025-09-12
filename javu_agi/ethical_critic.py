from __future__ import annotations
import os, json, time
from typing import Any, Dict
from javu_agi.llm_router import route_and_generate

_DEFAULT_PRINCIPLES = [
    "pro-human, damai, toleran, anti-kekerasan",
    "pro-lingkungan & keberlanjutan",
    "anti-penipuan, anti-eksploitasi, patuh hukum",
    "hormati privasi, data minimization",
    "hindari bias, diskriminasi, ujaran kebencian",
]


def _principles() -> str:
    s = os.getenv("ETHICS_PRINCIPLES")
    return s if s else "; ".join(_DEFAULT_PRINCIPLES)


def _ask(model: str, prompt: str) -> Dict[str, Any]:
    r = route_and_generate(
        model=model, prompt=prompt, temperature=0.0, distill_log=False
    )
    try:
        return json.loads(r.get("text", "{}"))
    except Exception:
        return {"safe": True, "decision": "allow", "reasons": ["fallback"]}


def precheck(user_text: str) -> Dict[str, Any]:
    model = os.getenv("ETHICS_MODEL", "gpt-4o-mini")
    pj = f"""You are an ethics gate. Given USER text, decide JSON: {{"safe":bool,"decision":"allow|revise|block","reasons":[str]}}.
Principles: {_principles()}
USER: {user_text}"""
    return _ask(model, pj)


def postcheck(final_text: str) -> Dict[str, Any]:
    model = os.getenv("ETHICS_MODEL", "gpt-4o-mini")
    pj = f"""You are an ethics auditor. Given ASSISTANT text, decide JSON: {{"safe":bool,"decision":"allow|revise|block","reasons":[str]}}.
Principles: {_principles()}
ASSISTANT: {final_text}"""
    return _ask(model, pj)
