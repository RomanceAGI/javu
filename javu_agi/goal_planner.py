from __future__ import annotations
import os, time, json
from typing import Any, Dict, List, Optional

from javu_agi.audit_chain import AuditChain
from javu_agi.planner import Planner
from javu_agi.eco_guard import EcoGuard
from javu_agi.planet.eco_guard import SustainabilityGuard, PlanetaryPolicy

# Legacy dependency kept for strict backward-compat (only for fallback formatting)
from javu_agi.llm import call_llm

_AUDIT = AuditChain(log_dir=os.getenv("AUDIT_CHAIN_DIR", "logs/audit_chain"))
_ECO = EcoGuard()
_PG = PlanetaryGuardian()

_DEFAULT_STEP_CAP = int(os.getenv("GOAL_STEP_CAP", "12"))


class GoalPlanner:
    """
    Planner tujuan tingkat proyek:
    - Intent → langkah → enrichment domain (via Planner universal)
    - Safety (Eco/Planet) pre + post
    - Output: struktur JSON + formatter markdown bullets (compat)
    """

    def __init__(
        self, *, use_skillgraph: bool = True, step_cap: int = _DEFAULT_STEP_CAP
    ):
        self.core = Planner(use_skillgraph=use_skillgraph)
        self.step_cap = step_cap

    def plan(
        self, goal_text: str, meta: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        t0 = time.time()
        meta = meta or {}

        # 1) All-domain planning (intent→steps→evidence→rank) via universal planner
        base = self.core.plan(goal_text)
        if base.get("status") != "ok":
            _AUDIT.commit(
                "goal_planner:block",
                {"status": base.get("status"), "safety": base.get("safety")},
            )
            return {
                "status": "blocked",
                "reason": base.get("safety") or base.get("hint") or "planner_blocked",
            }

        steps = base.get("steps", [])[: self.step_cap]

        # 2) Safety post-enrichment recheck (fail-closed)
        eco = _ECO.score(task=goal_text, plan=json.dumps(steps)[:2000])
        pg = _PG.assess(steps)
        if not (eco.get("allow", True) and pg.get("permit", True)):
            _AUDIT.commit("goal_planner:veto_post", {"eco": eco, "planet": pg})
            return {
                "status": "blocked",
                "reason": "eco_or_planetary_veto",
                "eco": eco,
                "planet": pg,
            }

        # 3) Projectize: tambahkan struktur *who/when/risk* bila tersedia di meta
        owner = meta.get("owner") or os.getenv("DEFAULT_OWNER") or "owner:n/a"
        budget = float(meta.get("budget_usd") or os.getenv("DEFAULT_BUDGET_USD", "0"))
        due = meta.get("due_date") or os.getenv(
            "DEFAULT_DUE_DATE"
        )  # ISO string opsional

        proj_steps: List[Dict[str, Any]] = []
        for i, s in enumerate(steps, start=1):
            proj_steps.append(
                {
                    "id": f"S{i:02d}",
                    "desc": s.get("desc") or s,
                    "tool": s.get("tool"),
                    "cmd": s.get("cmd"),
                    "owner": owner,
                    "eta_days": s.get("eta_days", 1),
                    "risk": s.get(
                        "risk", 0.2
                    ),  # default rendah, bisa diupdate pas eksekusi
                }
            )

        out = {
            "status": "ok",
            "intent": base.get("intent"),
            "domains": base.get("domains", []),
            "confidence": base.get("confidence", 0.6),
            "owner": owner,
            "budget_usd": budget,
            "due_date": due,
            "steps": proj_steps[: self.step_cap],
            "ms": base.get("ms"),
        }
        _AUDIT.commit(
            "goal_planner:final",
            {"n_steps": len(out["steps"]), "conf": out["confidence"]},
        )
        return out

    @staticmethod
    def to_bullets(plan: Dict[str, Any]) -> str:
        """Formatter markdown bullets (compat ke output lama)."""
        if plan.get("status") != "ok":
            reason = plan.get("reason", "blocked")
            return f"- STATUS: {plan.get('status')}\n- REASON: {reason}"
        lines = []
        lines.append(f"- Status: OK")
        if plan.get("domains"):
            lines.append(f"- Domain: {', '.join(plan['domains'])}")
        lines.append(f"- Confidence: {plan.get('confidence', 0.6):.2f}")
        if plan.get("owner"):
            lines.append(f"- Owner: {plan['owner']}")
        if plan.get("due_date"):
            lines.append(f"- Due: {plan['due_date']}")
        if plan.get("budget_usd", 0) > 0:
            lines.append(f"- Budget: ${plan['budget_usd']:.2f}")
        # steps
        for i, s in enumerate(plan.get("steps", []), start=1):
            desc = s.get("desc") if isinstance(s, dict) else str(s)
            lines.append(f"- Langkah {i}: {desc}")
        return "\n".join(lines)


# Legacy function (kept for backward-compat)


def generate_plan_from_goal(goal_text: str) -> str:
    """
    Kompatibel dengan versi lama:
    - Dulu: prompt langsung → bullets.
    - Sekarang: lewat Planner universal + safety + audit → bullets rapi.
    """
    planner = GoalPlanner(use_skillgraph=True)
    plan = planner.plan(goal_text)
    md = planner.to_bullets(plan)
    return md
