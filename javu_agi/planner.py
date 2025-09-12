from __future__ import annotations
import os, time, json, re, pkgutil, importlib, traceback
from typing import Any, Dict, List, Tuple, Optional, Callable

from javu_agi.llm import call_llm
from javu_agi.audit.audit_chain import AuditChain
from javu_agi.eco_guard import EcoGuard

try:
    from javu_agi.learn.skill_graph import SkillGraph
except Exception:
    SkillGraph = None

AUDIT = AuditChain(log_dir=os.getenv("AUDIT_CHAIN_DIR", "logs/audit_chain"))
_ECO = EcoGuard()
_PG = PlanetaryGuardian()


# ------------------------- Legacy (compat) -------------------------
def detect_agent_via_llm(user_input: str) -> str:
    sys = "Kamu adalah AGI classifier."
    prompt = f"User: {user_input}\nOutput:"
    resp = call_llm(
        prompt=prompt, system_prompt=sys, temperature=0.0, task_type="analyze"
    ).strip()
    return resp


class LegacyPlanner:
    def plan(self, query: str) -> Dict[str, Any]:
        role = detect_agent_via_llm(query)
        steps = [
            {"desc": "Klarifikasi masalah"},
            {"desc": "Cek knowledge base"},
            {"desc": "Tawarkan solusi ringkas"},
        ]
        eco = _ECO.score(task=query, plan=json.dumps(steps))
        pg = _PG.assess(steps)
        permit = bool(eco.get("allow", True)) and bool(pg.get("permit", True))
        AUDIT.commit("legacy_planner", {"role": role, "permit": permit})
        return {"status": "ok" if permit else "blocked", "role": role, "steps": steps}


# ------------------------- Domain Registry -------------------------
# Enricher signature: (query:str, intent:dict, steps:list[dict]) -> list[dict]
Enricher = Callable[[str, Dict[str, Any], List[Dict[str, Any]]], List[Dict[str, Any]]]
Matcher = Callable[[str], float]  # returns confidence 0..1


class DomainRegistry:
    def __init__(self):
        self._items: List[Tuple[str, Matcher, Enricher]] = []
        self._loaded = False

    def register(self, name: str, matcher: Matcher, enricher: Enricher):
        self._items.append((name, matcher, enricher))

    def load_dynamic(self):
        """Scan javu_agi/domains/*.py for ENRICHERS dict = {name: (matcher, enricher)}."""
        if self._loaded:
            return
        self._loaded = True
        try:
            import javu_agi.domains as _dompkg  # type: ignore
        except Exception:
            return
        for m in pkgutil.iter_modules(_dompkg.__path__):
            try:
                mod = importlib.import_module(f"javu_agi.domains.{m.name}")
                ENRICHERS = getattr(mod, "ENRICHERS", {})
                for name, pair in ENRICHERS.items():
                    matcher, enricher = pair
                    self.register(name, matcher, enricher)
            except Exception:
                # don't fail; continue
                traceback.print_exc()

    def infer(self, query: str, k: int = 5) -> List[Tuple[str, float, Enricher]]:
        """Return top-k domains by matcher score + optional LLM assist."""
        self.load_dynamic()
        scored = []
        for name, matcher, enricher in self._items:
            try:
                s = float(max(0.0, min(1.0, matcher(query))))
            except Exception:
                s = 0.0
            if s > 0.0:
                scored.append((name, s, enricher))
        # Heuristic rules (broad ontology keywords)
        HEUR: List[Tuple[str, List[str]]] = [
            (
                "agriculture",
                ["farm", "crop", "soil", "irrigat", "harvest", "pupuk", "benih"],
            ),
            ("oil_gas", ["rig", "pipeline", "refinery", "flare", "mining", "frack"]),
            (
                "infrastructure",
                ["bridge", "rail", "dam", "concrete", "cement", "road", "highway"],
            ),
            (
                "healthcare",
                ["clinic", "hospital", "diagnosis", "medical", "patient", "ICD"],
            ),
            (
                "finance",
                ["bank", "loan", "credit", "ledger", "invoice", "portfolio", "risk"],
            ),
            (
                "education",
                ["school", "university", "curriculum", "exam", "quiz", "course"],
            ),
            (
                "manufacturing",
                ["factory", "assembly", "CNC", "qc", "supply chain", "bom"],
            ),
            ("retail", ["store", "ecommerce", "cart", "checkout", "sku"]),
            ("logistics", ["warehouse", "fleet", "route", "last mile"]),
            ("energy", ["solar", "wind", "battery", "grid", "inverter"]),
            (
                "ai_ml",
                ["dataset", "inference", "embedding", "fine-tune", "prompt", "agent"],
            ),
            ("software_eng", ["repo", "api", "service", "docker", "k8s", "ci/cd"]),
            (
                "game_dev",
                ["unity", "unreal", "sprite", "prefab", "shader", "controller"],
            ),
            ("legal", ["contract", "agreement", "compliance", "regulation"]),
            ("gov_public", ["policy", "procurement", "public sector", "tender"]),
        ]
        lowq = query.lower()
        for name, kws in HEUR:
            if any(k in lowq for k in kws):
                # append only if not already present
                if not any(name == t[0] for t in scored):
                    scored.append(
                        (name, 0.51, _GENERIC_ENRICHERS.get(name, generic_enricher))
                    )
        # Optional: LLM assist to suggest domains textually
        try:
            sys = "Sebutkan 3-6 domain relevan (kata tunggal lowercase, koma) untuk tugas berikut."
            resp = call_llm(
                prompt=query, system_prompt=sys, temperature=0.0, task_type="classify"
            )
            for tok in re.split(r"[,/]|\\n|\\s", resp.lower()):
                tok = tok.strip()
                if not tok:
                    continue
                if not any(tok == t[0] for t in scored):
                    scored.append((tok, 0.5, generic_enricher))
        except Exception:
            pass
        # sort & top-k
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:k]


# ------------------------- Generic Enrichers -------------------------
def _append(steps: List[Dict[str, Any]], *more: Dict[str, Any], cap: int = 12):
    steps.extend(more)
    if len(steps) > cap:
        del steps[cap:]


def generic_enricher(
    query: str, intent: Dict[str, Any], steps: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """Safe defaults for unknown domains."""
    _append(
        steps,
        {"desc": "Add metrics & logging for each step"},
        {"desc": "Define success criteria & rollback plan"},
    )
    return steps


def _mk_enricher(extra_steps: List[Dict[str, Any]]) -> Enricher:
    def _enr(
        query: str, intent: Dict[str, Any], steps: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        _append(steps, *extra_steps)
        return steps

    return _enr


_GENERIC_ENRICHERS: Dict[str, Enricher] = {
    "agriculture": _mk_enricher(
        [
            {"desc": "Assess soil/water impact & biodiversity"},
            {"desc": "Check local regulations & pesticide limits"},
        ]
    ),
    "oil_gas": _mk_enricher(
        [
            {"desc": "Quantify CO2e & methane flaring; propose mitigation"},
            {"desc": "Add safety & spill response checklist"},
        ]
    ),
    "infrastructure": _mk_enricher(
        [
            {"desc": "Material durability & lifecycle analysis"},
            {"desc": "Environmental impact & community consent"},
        ]
    ),
    "healthcare": _mk_enricher(
        [
            {"desc": "HIPAA/PII safeguard & consent validation"},
            {"desc": "Clinical validation & harm analysis"},
        ]
    ),
    "finance": _mk_enricher(
        [
            {"desc": "Segregate duties, audit trail, and fraud checks"},
            {"desc": "Stress test risk model; regulatory compliance"},
        ]
    ),
    "education": _mk_enricher(
        [
            {"desc": "Learning objectives mapping & fairness checks"},
            {"desc": "Accessibility & offline mode planning"},
        ]
    ),
    "manufacturing": _mk_enricher(
        [
            {"desc": "Quality control plan & SPC"},
            {"desc": "Worker safety and energy optimization"},
        ]
    ),
    "retail": _mk_enricher(
        [
            {"desc": "PCI & payment compliance; inventory accuracy"},
            {"desc": "Customer privacy & consent preferences"},
        ]
    ),
    "logistics": _mk_enricher(
        [
            {"desc": "Route optimization with fuel/CO2 constraints"},
            {"desc": "Cold-chain/fragile handling SOPs"},
        ]
    ),
    "energy": _mk_enricher(
        [
            {"desc": "Grid stability & peak shaving"},
            {"desc": "Green scheduling & energy source disclosure"},
        ]
    ),
    "ai_ml": _mk_enricher(
        [
            {"desc": "No fine-tune: use prompt/SkillGraph only"},
            {"desc": "Bias/fairness eval & data privacy"},
        ]
    ),
    "software_eng": _mk_enricher(
        [
            {"desc": "Threat modeling & SLOs"},
            {"desc": "CI/CD with preflight & rollback"},
        ]
    ),
    "game_dev": _mk_enricher(
        [
            {"desc": "Performance budget (fps/mem) & playtest loop"},
            {"desc": "Content rating & anti-cheat policy"},
        ]
    ),
    "legal": _mk_enricher(
        [
            {"desc": "Jurisdiction & compliance matrix"},
            {"desc": "Counterparty risk & clause validation"},
        ]
    ),
    "gov_public": _mk_enricher(
        [
            {"desc": "Public interest impact, transparency & auditability"},
            {"desc": "Procurement policy compliance & citizen privacy"},
        ]
    ),
}


# ------------------------- Universal Planner -------------------------
class Planner:
    """
    All-domain universal planner:
      1) Intent parse + uncertainty
      2) Draft high-level steps (SkillGraph expand opsional)
      3) Safety gate (EcoGuard + PlanetaryGuardian)
      4) Evidence gate (rationale + checks saat uncertainty tinggi)
      5) Rank & finalize
      + Domain enrichment pipeline (multi-domain), safety re-check
    """

    def __init__(
        self, *, use_skillgraph: bool = True, max_domains: int = 4, step_cap: int = 12
    ):
        self.use_sg = use_skillgraph and (SkillGraph is not None)
        self.sg = (
            SkillGraph(cache_dir=os.getenv("SKILL_CACHE_DIR", "/data/skill_cache"))
            if self.use_sg
            else None
        )
        self.uncertainty_cap = float(os.getenv("PLANNER_UNCERTAINTY_MAX", "0.65"))
        self.step_cap = step_cap
        self.domreg = DomainRegistry()
        # register built-in generic enrichers as default matchers
        for name, enr in _GENERIC_ENRICHERS.items():
            self.domreg.register(
                name,
                matcher=lambda q, n=name: (
                    0.6 if any(k in q.lower() for k in n.split("_")) else 0.0
                ),
                enricher=enr,
            )
        self.max_domains = max_domains

    # 1) Intent + uncertainty
    def parse_intent(self, query: str) -> Dict[str, Any]:
        sys = "Ekstrak intent, goals[], constraints[], uncertainty∈[0,1]. Balas JSON valid."
        prompt = f'Input:\n{query}\nBalas JSON: {{"intent":..., "goals":[], "constraints":[], "uncertainty":0.xx}}'
        out = call_llm(
            prompt=prompt, system_prompt=sys, temperature=0.1, task_type="analyze"
        )
        try:
            js = json.loads(out)
        except Exception:
            js = {
                "intent": "generic",
                "goals": [query[:64]],
                "constraints": [],
                "uncertainty": 0.4,
            }
        js["uncertainty"] = float(max(0.0, min(1.0, js.get("uncertainty", 0.5))))
        AUDIT.commit("planner:parse_intent", {"uncertainty": js["uncertainty"]})
        return js

    # 2) Draft steps (+SkillGraph)
    def draft_steps(self, intent: Dict[str, Any]) -> List[Dict[str, Any]]:
        sys = 'Buat rencana 4-10 langkah JSON: [{"desc":..., "tool"?:..., "cmd"?:...}]'
        prompt = f"Intent:{intent.get('intent')} Goals:{intent.get('goals')} Constraints:{intent.get('constraints')}"
        out = call_llm(
            prompt=prompt, system_prompt=sys, temperature=0.2, task_type="plan"
        )
        try:
            steps = json.loads(out)
            if not isinstance(steps, list):
                raise ValueError("not list")
        except Exception:
            steps = [
                {"desc": "Analyze problem"},
                {"desc": "Propose safe approach"},
                {"desc": "Execute minimal safe step"},
                {"desc": "Evaluate outcome"},
            ]
        if self.sg:
            try:
                steps = self.sg.expand_and_cache(steps)
            except Exception:
                pass
        return steps[: self.step_cap]

    # 3) Safety gate awal
    def safety_gate(
        self, query: str, steps: List[Dict[str, Any]]
    ) -> Tuple[bool, Dict[str, Any]]:
        eco = _ECO.score(task=query, plan=json.dumps(steps)[:2000])
        pg = _PG.assess(steps)
        permit = bool(eco.get("allow", True)) and bool(pg.get("permit", True))
        rec = {"eco": eco, "planet": pg, "permit": permit}
        if not permit:
            AUDIT.commit("planner:veto_pre", rec)
        return permit, rec

    # 4) Evidence gate
    def evidence_gate(
        self, query: str, steps: List[Dict[str, Any]], uncertainty: float
    ) -> Tuple[bool, Dict[str, Any]]:
        if uncertainty < self.uncertainty_cap:
            return True, {"rationale": "low-uncertainty", "checks": []}
        sys = "Berikan rationale singkat + 3 checks (heuristik/evidence) mendukung rencana. JSON: {rationale, checks[]}"
        prompt = f"Query:{query}\nSteps:{steps}"
        out = call_llm(
            prompt=prompt, system_prompt=sys, temperature=0.0, task_type="reason"
        )
        ok = True
        try:
            ev = json.loads(out)
        except Exception:
            ok, ev = False, {"rationale": "-", "checks": []}
        AUDIT.commit(
            "planner:evidence", {"ok": ok, "n_checks": len(ev.get("checks", []))}
        )
        return ok, ev

    # Domain enrichment pipeline (multi-domain)
    def enrich_domains(
        self, query: str, intent: Dict[str, Any], steps: List[Dict[str, Any]]
    ) -> Tuple[List[str], List[Dict[str, Any]]]:
        cand = self.domreg.infer(query, k=self.max_domains)
        domains: List[str] = []
        for name, score, enricher in cand:
            try:
                steps = enricher(query, intent, steps)
                domains.append(name)
                if len(steps) > self.step_cap:
                    steps = steps[: self.step_cap]
            except Exception:
                traceback.print_exc()
        AUDIT.commit("planner:domains", {"domains": domains})
        return domains, steps

    # 5) Rank & finalize
    def rank_and_pack(
        self, steps: List[Dict[str, Any]], evidence: Dict[str, Any]
    ) -> Dict[str, Any]:
        sys = "Skor langkah (impact/safety/feasibility 0..1) & overall confidence. JSON: {steps:[{...score}], confidence}"
        prompt = f"Steps:{steps}\nEvidence:{evidence}"
        out = call_llm(
            prompt=prompt, system_prompt=sys, temperature=0.1, task_type="analyze"
        )
        try:
            ranked = json.loads(out)
        except Exception:
            ranked = {"steps": steps, "confidence": 0.6}
        ranked["confidence"] = float(max(0.0, min(1.0, ranked.get("confidence", 0.6))))
        AUDIT.commit("planner:rank", {"confidence": ranked["confidence"]})
        return ranked

    # Entrypoint
    def plan(self, query: str) -> Dict[str, Any]:
        t0 = time.time()
        intent = self.parse_intent(query)
        steps = self.draft_steps(intent)
        permit, safety = self.safety_gate(query, steps)
        if not permit:
            return {"status": "blocked", "safety": safety}
        eg_ok, evidence = self.evidence_gate(
            query, steps, intent.get("uncertainty", 0.5)
        )
        if not eg_ok:
            return {
                "status": "needs_evidence",
                "hint": "auto-evidence insufficient",
                "proposed_steps": steps,
            }
        # all-domain enrichment
        domains, steps = self.enrich_domains(query, intent, steps)
        # safety re-check after enrichment
        permit2, safety2 = self.safety_gate(query, steps)
        if not permit2:
            return {"status": "blocked", "safety": safety2, "domains": domains}
        ranked = self.rank_and_pack(steps, evidence)
        AUDIT.commit(
            "planner:final",
            {
                "ms": int((time.time() - t0) * 1000),
                "n_steps": len(steps),
                "domains": domains,
            },
        )
        return {
            "status": "ok",
            "intent": intent,
            "domains": domains,
            "steps": ranked.get("steps", steps),
            "confidence": ranked.get("confidence", 0.6),
            "ms": int((time.time() - t0) * 1000),
        }
