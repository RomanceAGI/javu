from __future__ import annotations
import math, random
from typing import List, Dict, Any, Tuple


class MCTSPlanner:
    def __init__(
        self,
        world,
        llm_planner,
        skill_graph,
        gamma: float = 0.97,
        c_ucb: float = 1.2,
        horizon: int = 8,
        widen_k: int = 6,
    ):
        self.world = world
        self.llm = llm_planner
        self.graph = skill_graph
        self.gamma = gamma
        self.c_ucb = c_ucb
        self.horizon = horizon
        self.widen_k = widen_k

    def _cands(
        self, prompt: str, partial: List[Dict[str, str]]
    ) -> List[Dict[str, str]]:
        # Ambil kandidat dari LLM + SkillGraph; dedup per (tool,cmd)
        c = []
        try:
            base = self.llm.plan(prompt).steps or []
            c += base[: self.widen_k]
        except Exception:
            pass
        try:
            sg = self.graph.expand_and_cache(base)[: self.widen_k]
            c += sg
        except Exception:
            pass
        # unik
        seen = set()
        out = []
        for s in c:
            key = (s.get("tool", "?"), s.get("cmd", ""))
            if key in seen:
                continue
            seen.add(key)
            out.append({"tool": key[0], "cmd": key[1]})
        return out[: self.widen_k]

    def _score_step(
        self, state_text: str, step: Dict[str, str], depth: int
    ) -> Tuple[float, Dict[str, float]]:
        a = f"{step.get('tool','')} {step.get('cmd','')}"
        pred = self.world.mb.predict(state_text, a)
        r, conf, risk = pred["reward"], pred["confidence"], pred["risk"]
        # value tail (approx)
        val = self.world.value_estimate(state_text, a)
        score = (self.gamma**depth) * (r + 0.2 * conf - 0.6 * risk) + 0.6 * val
        return score, pred

    def plan(self, prompt: str) -> List[Dict[str, str]]:
        state = self.world.current_state().as_text()
        root_children = self._cands(prompt, [])
        if not root_children:
            return []

        # simple MCTS: pick best next step by sim>=N rollouts
        N = max(24, 4 * len(root_children))
        stats = {i: {"n": 0, "q": 0.0, "pred": None} for i in range(len(root_children))}

        for t in range(N):
            # UCB select child
            best_i, best_ucb = 0, float("-inf")
            for i in range(len(root_children)):
                n, q = stats[i]["n"], stats[i]["q"]
                u = q + self.c_ucb * math.sqrt(math.log(t + 1) / (n + 1e-6))
                if u > best_ucb:
                    best_ucb, best_i = u, i
            s = root_children[best_i]
            sc, pred = self._score_step(state, s, depth=1)
            stats[best_i]["n"] += 1
            stats[best_i]["q"] += (sc - stats[best_i]["q"]) / stats[best_i]["n"]
            stats[best_i]["pred"] = pred

        # pilih langkah awal terbaik + lanjutkan horizon kedalaman kecil (greedy tail)
        first = max(range(len(root_children)), key=lambda i: stats[i]["q"])
        plan = [root_children[first]]

        # tail greedy sampai horizon
        for d in range(1, self.horizon):
            state_tail = (
                f"{state}\n>> {plan[-1].get('tool','')} {plan[-1].get('cmd','')}"
            )
            cands = self._cands(prompt, plan)
            if not cands:
                break
            best = max(
                cands, key=lambda st: self._score_step(state_tail, st, depth=d + 1)[0]
            )
            plan.append(best)
        return plan
