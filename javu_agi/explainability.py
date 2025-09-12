from __future__ import annotations
from typing import Dict, Any

TEMPLATE = (
    "Decision {id} → {verdict}. "
    "Norms: util={util:.2f}, deon={deon:.2f}, virtue={virtue:.2f}. "
    "Peace={peace:.2f}, Sustain={sustain:.2f}, Meaning={meaning:.2f}. "
    "Planet risk={eco}, Commons={commons}. Oversight={oversight}. "
    "Reason: {reason}."
)


def explain_decision(record: Dict[str, Any]) -> str:
    r = record.get("risk", {})
    return TEMPLATE.format(
        id=record.get("intent_id", "?"),
        verdict=record.get("verdict", "?"),
        util=r.get("utilitarian", r.get("moral", {}).get("utilitarian", 0.0)),
        deon=r.get("deontological", r.get("moral", {}).get("deontological", 0.0)),
        virtue=r.get("virtue", r.get("moral", {}).get("virtue", 0.0)),
        peace=r.get(
            "peace_score", r.get("dialogue", {}).get("votes", {}).get("pro", 0.0)
        ),
        sustain=r.get("sustainability_score", 0.0),
        meaning=r.get("meaning_score", 0.0),
        eco=r.get("planet", {}).get("eco_risk", r.get("eco_risk", "-")),
        commons=r.get("commons_safe", "-"),
        oversight=record.get("oversight", "-"),
        reason=record.get("reason", "-"),
    )
