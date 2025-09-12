from __future__ import annotations
from typing import Any, Dict, List, Tuple
import os, math, hashlib
from javu_agi.rag.retriever import HybridRetriever
from javu_agi.world.causal import CausalGraph
from javu_agi.mbrl import MBWorld
from javu_agi.state_space import StructuredState


class WorldModel:
    """
    World model PRO:
    - State fakta + RAG hybrid
    - CausalGraph (do-operator) untuk counterfactual
    - Simulasi aksi & rencana multi-step (simulate_plan)
    """

    def __init__(self):
        self.state: Dict[str, Any] = {
            "facts": [],
            "tools_used": [],
            "uncertainty": 0.25,
            "beliefs": {},
        }
        self._retriever = HybridRetriever(facts_ref=lambda: self.state.get("facts", []))
        self.cg = CausalGraph()
        self.cg.add_node("risk")
        self.cg.add_node("confidence")
        self.cg.add_edge("evidence_quality", "confidence", 0.6)
        self.cg.add_edge("ambiguity", "risk", 0.7)
        self.mb = MBWorld()
        self._last_state = StructuredState()
        use_ens = os.getenv("MBRL_ENSEMBLE", "1") == "1"

    def mb_predict(self, state: str, action: str):
        return self.mb.predict(state, action)

    def mb_update(self, state: str, action: str, reward: float, success: bool):
        self.mb.update(state, action, reward, success)
        self.mb.save()

    def current_state(self) -> StructuredState:
        return self._last_state

    def observe_tool(self, tool: str, stdout: str):
        try:
            self._last_state.update_from_tool(tool, stdout)
        except Exception:
            pass

    def value_estimate(self, prompt: str, plan_text: str) -> float:
        """Skor panjang-horizon (proxy): rata-rata reward rollout ringan."""
        try:
            pred = self.simulate_plan([plan_text])
            r = float(pred.get("expected_reward", 0.0))
            c = float(pred.get("expected_confidence", 0.0))
            k = 1.0 - (1.0 if pred.get("risk_level", "high") == "low" else 0.0)
            return 0.6 * r + 0.3 * c - 0.5 * k
        except Exception:
            return 0.0

    # -------- state ops --------
    def update_world_state(self, delta: Dict[str, Any]):
        self.state.update(delta)
        if "tool" in delta:
            self.state["tools_used"].append(delta["tool"])
        # optional: sink ke causal graph kalau ada sinyal numerik
        for k in ("evidence_quality", "ambiguity"):
            if k in delta:
                self.cg.set_value(k, delta[k])

    def estimate_uncertainty(self, query: str) -> float:
        ctx = self.retrieve_context(query, k=6)
        overlap = sum(
            1 for f in ctx if any(t in f.lower() for t in query.lower().split())
        )
        u = max(0.05, 1.0 / (1.0 + overlap + 0.5))
        u = 0.6 * u + 0.4 * float(self.state.get("uncertainty", 0.25))
        self.state["uncertainty"] = u
        # map ke node causal sebagai "ambiguity"
        self.cg.set_value("ambiguity", min(1.0, u))
        return round(min(max(u, 0.05), 0.95), 3)

    def measure_novelty(self, query: str) -> float:
        facts = self.state.get("facts", [])
        if not facts:
            return 0.7
        qset = set(query.lower().split())
        coverage = sum(1 for f in facts if qset & set(f.lower().split()))
        nov = 1.0 / (1 + coverage)
        return round(min(max(nov, 0.1), 0.95), 3)

    # -------- retrieval --------
    def retrieve_context(self, query: str, k: int = 8) -> List[str]:
        return self._retriever.retrieve(query, k=k)

    # -------- simulation --------
    def _risk_from_text(self, text: str) -> str:
        t = text.lower()
        risky = any(
            x in t
            for x in [
                "bahaya",
                "eksploit",
                "hack",
                "bocor",
                "privasi",
                "self-harm",
                "bom",
            ]
        )
        if risky:
            return "high"
        if len(t) > 2500:
            return "medium"
        return "low"

    def _confidence_seed(self, action: str) -> float:
        h = int(hashlib.md5(action.encode("utf-8")).hexdigest(), 16) % 1000
        base_conf = 0.45 + (h / 1000) * 0.45
        # uncertainty dampening
        return base_conf * (1.0 - 0.4 * float(self.state.get("uncertainty", 0.25)))

    def simulate_action(self, action: str) -> Dict[str, Any]:
        risk = self._risk_from_text(action)
        conf = self._confidence_seed(action)
        # causal consistency tweak
        self.cg.set_value(
            "evidence_quality", min(1.0, 0.3 + 0.7 * (len(action) / 1200.0))
        )
        out = self.cg.propagate(steps=1)
        conf = max(0.35, min(conf + 0.1 * (out.get("confidence", 0.0) - 0.5), 0.95))
        step_cost = 1 + math.log1p(len(action))
        return {
            "risk_level": risk,
            "expected_confidence": round(conf, 3),
            "step_cost": round(step_cost, 3),
        }

    def simulate_plan(self, steps: List[str]) -> Dict[str, Any]:
        """
        Simulasi rencana multi-step (list of actions).
        Menghasilkan aggregate risk/conf/cost + nodewise.
        """
        agg_risk = "low"
        agg_conf = 0.0
        agg_cost = 0.0
        nodes = []
        risk_rank = {"low": 0, "medium": 1, "high": 2}
        for s in steps:
            sim = self.simulate_action(s)
            nodes.append(sim)
            agg_cost += sim["step_cost"]
            agg_conf += sim["expected_confidence"]
            if risk_rank[sim["risk_level"]] > risk_rank[agg_risk]:
                agg_risk = sim["risk_level"]
        agg_conf = round(agg_conf / max(1, len(steps)), 3)
        return {
            "risk_level": agg_risk,
            "expected_confidence": agg_conf,
            "step_cost": round(agg_cost, 3),
            "nodes": nodes,
        }

    # -------- do-operator --------
    def do_intervene(
        self, assignments: Dict[str, float], probe: str = "confidence"
    ) -> float:
        """
        Counterfactual: set node values, propagate, baca probe (confidence/risk).
        """
        out = self.cg.do(assignments, steps=2)
        val = out.get(probe, 0.5)
        return float(val)
