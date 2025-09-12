from __future__ import annotations
from typing import List
from typing import Any, Dict
from javu_agi.planner import Planner
from javu_agi.audit.audit_chain import AuditChain
from javu_agi.llm import call_llm
import os, time


class HierarchicalPlanner:
    def __init__(self):
        self.core = Planner(use_skillgraph=True)
        self.audit = AuditChain(
            log_dir=os.getenv("AUDIT_CHAIN_DIR", "logs/audit_chain")
        )

    def plan(self, query: str) -> Dict[str, Any]:
        t0 = time.time()
        out = self.core.plan(query)
        self.audit.commit(
            "hplanner:plan",
            {"ms": int((time.time() - t0) * 1000), "status": out.get("status")},
        )
        return out


def decompose(goal: str) -> List[str]:
    prompt = f"""
Pecah goal berikut menjadi 5-7 subgoal yang terurut dan eksekutabel.
Goal: {goal}
Format: satu subgoal per baris, tanpa nomor.
"""
    resp = call_llm(prompt, task_type="plan", temperature=0.2, max_tokens=512)
    steps = [x.strip("- ").strip() for x in resp.splitlines() if x.strip()]
    return steps[:7]


def verify_subgoal(subgoal: str) -> bool:
    # light check via LLM
    ans = call_llm(
        f"Apakah subgoal ini well-formed dan aman? Jawab 'YES' atau 'NO'.\n{subgoal}",
        task_type="reflect",
        temperature=0.0,
        max_tokens=8,
    )
    return "YES" in ans.upper()


def plan_with_checks(goal: str) -> List[str]:
    steps = [s for s in decompose(goal) if verify_subgoal(s)]
    return steps
