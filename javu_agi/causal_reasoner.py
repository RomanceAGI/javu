from __future__ import annotations
import math, itertools, random
from typing import Dict, List, Tuple, Any


class CausalGraph:
    def __init__(self):
        self.parents = {}  # node -> set(parents)

    def add_edge(self, a: str, b: str):
        self.parents.setdefault(b, set()).add(a)
        self.parents.setdefault(a, set())

    def nodes(self):
        return list(self.parents.keys())

    def topo(self):
        indeg = {n: 0 for n in self.nodes()}
        for ch, ps in self.parents.items():
            for p in ps:
                indeg[ch] += 1
        S = [n for n, d in indeg.items() if d == 0]
        out = []
        while S:
            n = S.pop()
            out.append(n)
            for ch, ps in list(self.parents.items()):
                if n in ps:
                    ps.remove(n)
                    indeg[ch] -= 1
                    if indeg[ch] == 0:
                        S.append(ch)
        return out


class CausalReasoner:
    """
    Causal inference ringan tanpa training:
    - Build DAG heuristik dari teks task/plan
    - Hitung efek intervensi E[U | do(action)] via simulasi world_model (yang sudah ada)
    - Skor rencana dengan expected utility & risk-penalty
    """

    def __init__(self, world, values):
        self.world = world
        self.values = values

    def _extract_edges(self, prompt: str, steps: List[dict]) -> List[Tuple[str, str]]:
        txt = (prompt or "").lower()
        edges = []
        # heuristik trigger kata kausal
        triggers = [
            ("jika", "maka"),
            ("because", "then"),
            ("sebab", "akibat"),
            ("untuk", "sehingga"),
        ]
        for a, b in triggers:
            if a in txt and b in txt:
                try:
                    pre = txt.split(a, 1)[1].split(b, 1)[0].strip()[:32]
                    post = txt.split(b, 1)[1].strip()[:32]
                    if pre and post:
                        edges.append((pre, post))
                except Exception:
                    pass
        # dari langkah
        for s in steps or []:
            tool = (s.get("tool") or "step").lower()
            cmd = (s.get("cmd") or "").strip().lower()
            if not cmd:
                continue
            edges.append((tool, cmd[:48]))
        return edges[:20]

    def build_graph(self, prompt: str, steps: List[dict]) -> CausalGraph:
        g = CausalGraph()
        for a, b in self._extract_edges(prompt, steps):
            if a != b:
                g.add_edge(a, b)
        return g

    def _utility(self, prompt: str, step: dict) -> float:
        # pakai world model + nilai prososial
        try:
            conf = float(self.world.value_estimate(prompt, step.get("cmd", "")))  # 0..1
        except Exception:
            conf = 0.5
        # shaping prososial & lingkungan
        shaped = self.values.shape(conf, {"human_impact": 1.0, "env_impact": 0.7})
        return max(0.0, min(1.0, shaped))

    def recommend(self, prompt: str, steps: List[dict]) -> List[dict]:
        """Return steps sorted by causal expected utility (Monte Carlo kecil)."""
        if not steps:
            return []
        g = self.build_graph(prompt, steps)
        order = g.topo() or [s.get("cmd", "") for s in steps]
        scored = []
        for s in steps:
            u = self._utility(prompt, s)
            # Monte Carlo via simulator
            try:
                sim = self.world.simulate_action(s)
                risk = 0.0 if sim.get("risk_level", "low") == "low" else 0.3
                conf = float(sim.get("expected_confidence", 0.6))
            except Exception:
                risk, conf = 0.1, 0.6
            # bonus jika step mendahului banyak child di DAG
            deg = sum(1 for ch, ps in g.parents.items() if s.get("cmd", "") in ps)
            bonus = 0.03 * deg
            score = u * conf - risk + bonus
            scored.append((score, s))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [s for _, s in scored]
