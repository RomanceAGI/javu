from __future__ import annotations
from typing import Dict, List, Tuple, Any
import math, uuid


class CausalGraph:
    """Directed causal graph dengan bobot (0..1) + nilai key->state."""

    def __init__(self):
        self.nodes: Dict[str, Dict[str, Any]] = {}
        self.edges: List[Tuple[str, str, float]] = []  # (cause, effect, strength)

    def add_node(self, name: str, value: Any = None):
        self.nodes.setdefault(name, {"value": value})

    def set_value(self, name: str, value: Any):
        self.add_node(name)
        self.nodes[name]["value"] = value

    def add_edge(self, cause: str, effect: str, strength: float = 0.6):
        self.add_node(cause)
        self.add_node(effect)
        strength = max(0.0, min(1.0, strength))
        self.edges.append((cause, effect, strength))

    def propagate(self, steps: int = 2) -> Dict[str, Any]:
        """Propagation linear sederhana: effect += strength * cause (jika numerik)."""
        vals = {k: v.get("value", 0.0) for k, v in self.nodes.items()}
        for _ in range(max(1, steps)):
            delta = {}
            for c, e, s in self.edges:
                cv = _num(vals.get(c, 0))
                ev = _num(vals.get(e, 0))
                delta[e] = delta.get(e, 0.0) + s * cv
            for k, d in delta.items():
                vals[k] = 0.7 * _num(vals.get(k, 0)) + 0.3 * d
        return vals

    def do(self, interventions: Dict[str, Any], steps: int = 2) -> Dict[str, Any]:
        """Pearl-style do(): set nilai node lalu propagate tanpa mengubah edges."""
        # snapshot
        snap = {k: v.get("value", None) for k, v in self.nodes.items()}
        try:
            for k, v in interventions.items():
                self.set_value(k, v)
            out = self.propagate(steps=steps)
        finally:
            for k, v in snap.items():
                self.set_value(k, v)
        return out


def _num(x):
    try:
        return float(x)
    except Exception:
        return 0.0
