from __future__ import annotations
import os, json
from typing import Any, Dict
from javu_agi.llm_router import route_and_generate


def refine(text: str, persona: str = "calm, respectful, pro-human, tolerant") -> str:
    model = os.getenv("COACH_MODEL", "gpt-4o-mini")
    p = f"Rewrite ASSISTANT text to be concise, helpful, {persona}. Keep facts. Return only text.\nASSISTANT:\n{text}"
    r = route_and_generate(model=model, prompt=p, temperature=0.2, distill_log=False)
    return r.get("text", text) or text
