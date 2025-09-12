from __future__ import annotations
from typing import Dict, Any, List


def _heuristic_score(cand: Dict[str, Any]) -> float:
    sim = cand.get("sim", {})
    conf = float(sim.get("expected_confidence", 0.5))
    risk = sim.get("risk_level", "low")
    draft = str(cand.get("draft", ""))[:4000]

    # risk penalty
    rpen = {"low": 0.0, "medium": 0.15, "high": 0.4}.get(risk, 0.2)
    # length penalty (terlalu panjang rawan halu)
    lpen = 0.0
    if len(draft) > 1800:
        lpen = 0.1
    if len(draft) > 3000:
        lpen = 0.18

    vals = cand.get("values", {})
    peace = float(vals.get("peace_impact", 0.0))
    eco = float(vals.get("env_impact", 0.0))
    human = float(vals.get("human_impact", 0.0))
    vbonus = 0.05 * peace + 0.05 * eco + 0.10 * human

    return max(0.0, conf - rpen - lpen)


def evaluate_candidates(
    user_id: str, prompt: str, candidates: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    PRO: pilih kandidat secara robust.
    - Fallback deterministic kalau LLM evaluator gagal.
    - Return: {"mode_index": int, "text": str, "confidence": float, "risk": str}
    """
    if not candidates:
        return {
            "mode_index": 0,
            "text": "[no-candidate]",
            "confidence": 0.0,
            "risk": "low",
        }

    # skor heuristik
    scores = [_heuristic_score(c) for c in candidates]
    idx = max(range(len(scores)), key=lambda i: scores[i])
    best = candidates[idx]
    sim = best.get("sim", {})

    return {
        "mode_index": idx,
        "text": best.get("draft", ""),
        "confidence": float(sim.get("expected_confidence", 0.6)),
        "risk": sim.get("risk_level", "low"),
        "why": {"scores": scores},
    }
