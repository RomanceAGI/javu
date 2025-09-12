from typing import List, Dict, Any
import statistics as st


class Deliberator:
    def __init__(self, router, n: int = 3):
        self.router, self.n = router, max(1, n)

    def _ask(self, sys_prompt: str, user_prompt: str) -> str:
        # panggil router; no training, hanya inference
        return self.router.generate(system=sys_prompt, prompt=user_prompt)

    def run(self, prompt: str, plan_steps: List[Dict[str, Any]]) -> Dict[str, Any]:
        sys = "You are a careful, ethical, prosocial reasoner. Provide justification and risks."
        votes, reasons = [], []
        q = f"Evaluate this plan for safety, ethics, and effectiveness. Plan: {plan_steps}"
        for _ in range(self.n):
            try:
                ans = self._ask(sys, q)
                reasons.append(ans)
                vote = (
                    1.0
                    if any(k in ans.lower() for k in ["safe", "ethical", "approve"])
                    else 0.0
                )
                votes.append(vote)
            except Exception:
                votes.append(0.0)
        conf = st.mean(votes) if votes else 0.0
        return {"consensus": conf, "reasons": reasons}
