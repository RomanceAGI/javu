from __future__ import annotations
from typing import List, Dict, Any
from javu_agi.executive_controller import ExecutiveController
from javu_agi.arena.checkers import check
from javu_agi.research.verifier import verify_hypothesis


def _context_for(exec: ExecutiveController, prompt: str) -> List[str]:
    mem = exec.memory.recall_context(prompt)
    sem = [f.content for f in mem["semantic"]]
    epi = [e.prompt for e in mem["episodic"]]
    wctx = exec.world.retrieve_context(prompt, k=8)
    return list(dict.fromkeys(sem + wctx + epi))[:12]


def answer_by_mode(exec: ExecutiveController, prompt: str, mode: str) -> Dict[str, Any]:
    ctx = _context_for(exec, prompt)
    if mode == "S1":
        out = exec.reasoner.fast_answer(prompt, ctx)
    elif mode == "S2":
        out = exec.reasoner.deliberate_answer(prompt, ctx)
    else:
        hyps = exec.reasoner.generate_hypotheses(prompt, ctx, n=3)
        out = exec.reasoner.hypothesis_driven(prompt, ctx, hyps)
    # bonus verifikasi ilmiah jika S3
    score = 0.0
    if mode == "S3":
        ver = verify_hypothesis(out)
        score = float(ver["score"])
    return {"text": out, "science_score": score}


def duel(
    exec: ExecutiveController, prompt: str, rule: Dict, modes=("S2", "S3")
) -> Dict[str, Any]:
    a = answer_by_mode(exec, prompt, modes[0])
    b = answer_by_mode(exec, prompt, modes[1])
    a_ok = check(rule, a["text"])
    b_ok = check(rule, b["text"])
    # tie-breaker: science_score (untuk hipotesis)
    if a_ok and not b_ok:
        winner = modes[0]
    elif b_ok and not a_ok:
        winner = modes[1]
    elif a_ok and b_ok:
        winner = modes[1] if b["science_score"] > a["science_score"] else modes[0]
    else:
        winner = modes[1] if b["science_score"] > a["science_score"] else modes[0]
    return {"winner": winner, "A": a, "B": b}
