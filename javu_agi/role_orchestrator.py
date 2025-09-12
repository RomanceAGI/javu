from typing import Dict, Any
from javu_agi.llm_router import route_and_generate


def _ask(p, t=0.3, intent="general"):
    return route_and_generate(
        model=None, prompt=p, intent=intent, temperature=t, distill_log=False
    ).get("text", "")


def orchestrate(prompt: str) -> Dict[str, Any]:
    plan = _ask(f"Give numbered plan (max 5 steps) for: {prompt}", t=0.1)[:2000]
    if not plan.strip():
        return {"plan": "", "answer": "", "refined": "", "status": "plan_empty"}
    ans = _ask(f"Execute plan step-by-step strictly:\n{plan}\nKeep it concise.", t=0.2)[
        :4000
    ]
    ref = _ask(f"Critique and minimally fix factual/style errors:\n{ans}", t=0.0)[:4000]
    return {"plan": plan, "answer": ans, "refined": ref, "status": "ok"}
