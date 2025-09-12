from dataclasses import dataclass
from typing import List, Dict


@dataclass
class EthicsVerdict:
    allow: bool
    score: float
    rationale: str
    remedies: List[str]


class EthicsDeliberator:
    """
    Tri-axis: deontic (rule/policy), consequential (risk/benefit), virtue (values).
    Output transparan + saran mitigasi.
    """

    def __init__(self, policy, values):
        self.policy = policy  # e.g., AlignmentChecker / GovGuard
        self.values = values  # ValueMemory

    def evaluate(self, intent: str, plan_steps: List[Dict]) -> EthicsVerdict:
        # 1) Deontic: strict policy check (blockers absolut)
        deontic_block = []
        for s in plan_steps:
            ok, why = (
                self.policy.allows_step(s)
                if hasattr(self.policy, "allows_step")
                else (True, "")
            )
            if not ok:
                deontic_block.append(why)
        if deontic_block:
            return EthicsVerdict(
                False, 0.0, f"Deontic block: {deontic_block}", ["ubah tujuan/alat"]
            )

        # 2) Consequential: skoring sederhana risk/benefit (proxy)
        risk = sum(float(s.get("risk", 0.2)) for s in plan_steps)
        benefit = sum(float(s.get("benefit", 0.4)) for s in plan_steps)
        cons_score = max(0.0, min(1.0, benefit - 0.5 * risk))

        # 3) Virtue: keselarasan nilai (pro-human, pro-alam)
        vm = self.values.summary() if hasattr(self.values, "summary") else {}
        virtue_score = 0.5 + 0.5 * int("sustain" in str(vm).lower())

        score = 0.5 * cons_score + 0.5 * virtue_score
        allow = score >= 0.45
        rem = []
        if not allow or risk > benefit:
            rem.append(
                "minimize risk: pilih alat non-destruktif / data non-PII / read-only"
            )

        return EthicsVerdict(
            allow, score, f"cons={cons_score:.2f}, virtue={virtue_score:.2f}", rem
        )
