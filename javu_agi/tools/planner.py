from __future__ import annotations
from typing import List, Dict


class Plan:
    def __init__(self, steps: List[Dict]):
        self.steps = steps


class Planner:
    """
    Planner ringan: terjemah prompt → langkah-langkah tool.
    Nanti bisa diganti LLM/solver, kontraknya tetap.
    """

    def plan(self, prompt: str) -> Plan:
        p = prompt.lower()
        steps = []
        if any(k in p for k in ["ringkas", "summary", "resume"]):
            steps.append(
                {
                    "tool": "python",
                    "cmd": "python - <<'PY'\nprint('OK: ringkas placeholder')\nPY",
                }
            )
        if any(k in p for k in ["format", "urut", "sort"]):
            steps.append(
                {
                    "tool": "python",
                    "cmd": "python - <<'PY'\nprint(', '.join(sorted(['3','1','2'])))\nPY",
                }
            )
        if any(k in p for k in ["http://", "https://", "url", "crawl", "fetch"]):
            url = next(
                (
                    tok
                    for tok in prompt.split()
                    if tok.startswith(("http://", "https://"))
                ),
                "",
            )
            if url:
                steps.append({"tool": "bash", "cmd": f"curl -sSL {url} | head -n 120"})
        if not steps:
            steps.append(
                {"tool": "python", "cmd": "python - <<'PY'\nprint('NOOP')\nPY"}
            )
        return Plan(steps)
