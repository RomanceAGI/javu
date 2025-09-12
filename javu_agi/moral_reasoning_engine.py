from __future__ import annotations
import re, math, random, statistics
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple


@dataclass
class Argument:
    claim: str
    support: List[str] = field(default_factory=list)
    risk: float = 0.0
    benefit: float = 0.0
    duty_violation: float = 0.0
    virtue_alignment: float = 0.0

    def score(self, w: Dict[str, float]) -> float:
        # Higher is better for benefit & virtue; lower is better for risk & duty_violation
        return (
            self.benefit * w.get("benefit", 0.35)
            - self.risk * w.get("risk", 0.35)
            - self.duty_violation * w.get("duty", 0.20)
            + self.virtue_alignment * w.get("virtue", 0.10)
        )


class MoralReasoningEngine:
    FORBIDDEN = [
        r"\bkill\b",
        r"\btorture\b",
        r"\benslave\b",
        r"\bbioweapon\b",
        r"\bexploit\b",
        r"\bhate\s*speech\b",
        r"\bgenocide\b",
        r"\bterror\b",
    ]
    VIRTUES = [
        "kindness",
        "honesty",
        "compassion",
        "care",
        "courage",
        "temperance",
        "justice",
    ]

    def __init__(
        self, weights: Optional[Dict[str, float]] = None, seed: Optional[int] = None
    ):
        self.w = weights or {"benefit": 0.4, "risk": 0.4, "duty": 0.15, "virtue": 0.05}
        self._rng = random.Random(seed)

    def _text(self, plan: List[Dict[str, Any]]) -> str:
        return " \n".join(str(s) for s in (plan or []))

    def _scan_risk(self, text: str) -> float:
        r = 0.0
        for pat in self.FORBIDDEN:
            if re.search(pat, text, flags=re.I):
                r += 0.6
        if "leak" in text.lower() or "pii" in text.lower():
            r += 0.2
        return min(1.0, r)

    def _scan_benefit(self, text: str) -> float:
        b = 0.0
        for k in ["help", "benefit", "educate", "improve", "heal", "restore", "assist"]:
            b += text.lower().count(k) * 0.05
        return max(0.0, min(1.0, b))

    def _scan_duty(self, text: str) -> float:
        # 0=none, 1=heavy violation
        v = 0.0
        for k in ["illegal", "harm", "nonconsensual", "unauthorized"]:
            if k in text.lower():
                v += 0.25
        return max(0.0, min(1.0, v))

    def _scan_virtue(self, text: str) -> float:
        v = 0.0
        for k in self.VIRTUES:
            v += 0.07 if k in text.lower() else 0.0
        return max(0.0, min(1.0, v))

    def _extract_claims(self, plan: List[Dict[str, Any]]) -> List[str]:
        out = []
        for s in plan or []:
            cmd = (s.get("cmd") or str(s)).strip()
            if not cmd:
                continue
            out.append(cmd[:240])
        return out[:20]

    def analyze(
        self, plan: List[Dict[str, Any]], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        text = self._text(plan)
        claims = self._extract_claims(plan)
        args: List[Argument] = []
        for c in claims:
            t = c.lower()
            a = Argument(
                claim=c,
                risk=self._scan_risk(t),
                benefit=self._scan_benefit(t),
                duty_violation=self._scan_duty(t),
                virtue_alignment=self._scan_virtue(t),
                support=[f"evidence:{hash(c)%997}"],
            )
            args.append(a)
        if not args:
            return {"final": 0.0, "stance": "insufficient", "trace": []}
        scored = [(a.score(self.w), a) for a in args]
        scored.sort(key=lambda x: x[0], reverse=True)
        topk = scored[: min(5, len(scored))]
        final = statistics.mean(max(-1.0, min(1.0, s)) for s, _ in topk)
        stance = (
            "approve"
            if final > 0.2
            else ("escalate" if -0.2 <= final <= 0.2 else "deny")
        )
        trace = [
            {
                "claim": a.claim,
                "risk": round(a.risk, 3),
                "benefit": round(a.benefit, 3),
                "duty_violation": round(a.duty_violation, 3),
                "virtue_alignment": round(a.virtue_alignment, 3),
                "score": round(s, 3),
                "support": a.support,
            }
            for s, a in topk
        ]
        # counter-arg heuristic
        counter = []
        for s, a in topk:
            if a.risk > 0.3 or a.duty_violation > 0.3:
                counter.append({"against": a.claim, "reason": "risk/duty"})
        return {
            "final": round(final, 3),
            "stance": stance,
            "trace": trace,
            "counter": counter,
        }
