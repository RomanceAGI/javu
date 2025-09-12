from __future__ import annotations
from typing import List, Dict


def propose_intents(context: Dict, purpose: Dict, memory: Dict) -> List[Dict]:
    # generate kandidat niat di dalam mission envelope (tanpa retrain LLM)
    # contoh: improve_docs, reduce_energy, assist_user_goal, learn_new_skill
    return [{"name": "assist_user_goal", "why": "purpose"}, {"name": "reduce_energy"}]


def score_normative(intent: Dict, meters: Dict) -> Dict:
    # utility – risk + α*benefit_human + β*virtue_alignment – γ*uncertainty
    u = meters.get("utility", 0.5)
    r = meters.get("risk", 0.1)
    bh = meters.get("benefit_human", 0.4)
    va = meters.get("virtue_alignment", 0.5)
    uc = meters.get("uncertainty", 0.1)
    return {
        "final": u - r + 0.7 * bh + 0.5 * va - 0.6 * uc,
        "risk": r,
        "uncertainty": uc,
    }


def synthesize_intents(ctx, purpose, memory, meters_cb):
    cands = propose_intents(ctx, purpose, memory)
    scored = []
    for it in cands:
        meters = meters_cb(it)  # panggil evaluator internal lo
        sc = score_normative(it, meters)
        # filter keras (bounded autonomy)
        if sc["risk"] > 0.6 or sc["uncertainty"] > 0.35:
            continue
        scored.append((sc["final"], it))
    return [it for _, it in sorted(scored, reverse=True)[:3]]
