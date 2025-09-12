from __future__ import annotations
from dataclasses import dataclass
from typing import List, Dict, Any
import re


@dataclass
class NormConfig:
    w_util: float = 0.4
    w_deon: float = 0.4
    w_virtue: float = 0.2
    deny_if_deon_violation: bool = True


VIOLATIONS = [
    r"\bkill\b",
    r"\btorture\b",
    r"\benslave\b",
    r"\bexploit\b",
    r"\bbioweapon\b",
    r"\bhate\s*speech\b",
    r"\bterror\b",
    r"\bgenocide\b",
]
VIRTUES = ["kind", "honest", "care", "compassion", "courage", "temperance", "justice"]
BENEFIT_TOKENS = [
    "benefit",
    "help",
    "heal",
    "educate",
    "restore",
    "assist",
    "share",
    "collaborate",
]


class NormativeFramework:
    def __init__(self, cfg: NormConfig | None = None):
        self.cfg = cfg or NormConfig()

    def evaluate(
        self, plan: List[Dict[str, Any]], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        text = " \n".join(map(lambda s: str(s).lower(), plan))
        util = self._utilitarian(text, plan)
        deon, violations = self._deontological(text)
        virtue, virtues = self._virtue(text)

        final = (
            self.cfg.w_util * util + self.cfg.w_deon * deon + self.cfg.w_virtue * virtue
        )
        out = {
            "utilitarian": round(util, 3),
            "deontological": round(deon, 3),
            "virtue": round(virtue, 3),
            "violations": violations,
            "virtues_found": virtues,
            "final_score": round(final, 3),
            "stance": (
                "deny"
                if (self.cfg.deny_if_deon_violation and violations)
                else (
                    "approve"
                    if final >= 0.6
                    else "escalate" if final >= 0.45 else "deny"
                )
            ),
        }
        # Guidance
        if violations:
            out["guidance"] = "Remove deontic violations: " + ", ".join(violations[:3])
        elif out["stance"] != "approve":
            out["guidance"] = (
                "Increase benefit steps, explicitly add kindness/care, reduce risks."
            )
        else:
            out["guidance"] = "Proceed with monitoring."
        return out

    def _utilitarian(self, text: str, plan: List[Dict[str, Any]]) -> float:
        b = sum(text.count(k) for k in BENEFIT_TOKENS) * 0.04
        h = sum(text.count(k) for k in ["harm", "injury", "damage"]) * 0.06
        base = max(0.0, min(1.0, 0.3 + b - h))
        # bonus if plan includes sharing/cooperation
        if "share" in text or "collaborate" in text:
            base = min(1.0, base + 0.1)
        return base

    def _deontological(self, text: str) -> tuple[float, list[str]]:
        hits = [
            p.strip("\\b").replace("\\s*", " ")
            for p in VIOLATIONS
            if re.search(p, text, flags=re.I)
        ]
        return (0.0 if hits else 1.0, hits)

    def _virtue(self, text: str) -> tuple[float, list[str]]:
        found = [v for v in VIRTUES if v in text]
        score = 0.3 + 0.15 * min(3, len(found))
        return (min(1.0, score), found)
