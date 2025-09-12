from __future__ import annotations
from typing import Callable, Dict, Any, List

DebaterFn = Callable[[str, Dict[str, Any]], str]


class DebateEngine:
    """
    Multi-agent debate sederhana: k debater, r rounds, lalu judge.
    DebaterFn: (topic, ctx) -> argument string
    JudgeFn  : (arguments:list[str], ctx) -> verdict string
    """

    def __init__(
        self,
        debaters: List[DebaterFn],
        judge: Callable[[List[str], Dict[str, Any]], str],
    ):
        assert debaters and judge
        self.debaters = debaters
        self.judge = judge

    def debate(
        self, topic: str, ctx: Dict[str, Any] = None, rounds: int = 2
    ) -> Dict[str, Any]:
        ctx = dict(ctx or {})
        history: List[str] = []
        for r in range(rounds):
            for i, f in enumerate(self.debaters):
                try:
                    arg = f(topic, {"round": r, "idx": i, **ctx}) or ""
                except Exception:
                    arg = ""
                history.append(f"[d{i}·r{r}] {arg}")
        verdict = ""
        try:
            verdict = self.judge(history, ctx) or ""
        except Exception:
            verdict = ""
        return {"topic": topic, "history": history, "verdict": verdict}
