from dataclasses import dataclass
from typing import List, Dict


@dataclass
class Vote:
    name: str
    allow: bool
    reason: str
    score: float  # 0..1 (kepercayaan/etika)


class OversightBoard:
    """
    Gabung hasil dari: AlignmentChecker, EthicsDeliberator, GovGuard (dan lainnya).
    Kebijakan agregasi: veto deontik + rata2 skor untuk non-blockers.
    """

    def __init__(self, align, deliberator, gov):
        self.align = align
        self.delib = deliberator
        self.gov = gov

    def decide(self, prompt: str, steps: List[Dict]) -> Dict:
        votes: List[Vote] = []

        # GovGuard (deny-list cepat)
        ok_g, cat = (True, "")
        try:
            ok_g, cat = self.gov.check(prompt)
        except Exception:
            pass
        votes.append(Vote("GovGuard", ok_g, cat or "ok", 1.0 if ok_g else 0.0))

        # Alignment input
        try:
            gi = self.align.guard_input(prompt)
            votes.append(
                Vote(
                    "AlignIn",
                    bool(getattr(gi, "allow", True)),
                    getattr(gi, "category", "ok"),
                    0.8 if getattr(gi, "allow", True) else 0.0,
                )
            )
        except Exception:
            votes.append(Vote("AlignIn", True, "skip", 0.7))

        # Ethics deliberation (tri-axis)
        try:
            v = self.delib.evaluate(prompt, steps)
            votes.append(Vote("Ethics", v.allow, v.rationale, float(v.score)))
        except Exception:
            votes.append(Vote("Ethics", True, "skip", 0.6))

        # Keputusan agregat
        # Veto: kalau ada vote allow=False dari Gov/Align/Ethics → BLOCK
        if any(
            not x.allow for x in votes if x.name in {"GovGuard", "AlignIn", "Ethics"}
        ):
            return {
                "allow": False,
                "why": "; ".join(f"{x.name}:{x.reason}" for x in votes if not x.allow),
                "votes": [x.__dict__ for x in votes],
            }
        # Skor rata2 untuk logging
        score = sum(x.score for x in votes) / len(votes)
        return {"allow": True, "score": score, "votes": [x.__dict__ for x in votes]}
