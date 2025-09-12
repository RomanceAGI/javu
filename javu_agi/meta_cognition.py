from __future__ import annotations
from typing import List, Dict, Any


class MetaCognition:
    def critique(
        self, plan: List[Dict[str, Any]], reasoning_trace: List[str]
    ) -> Dict[str, Any]:
        if not reasoning_trace:
            return {
                "critique": "no reasoning trace",
                "confidence": 0.2,
                "advice": ["Expose reasoning steps."],
            }
        uniq = len(set(reasoning_trace))
        circ = uniq < (len(reasoning_trace) * 0.6)
        shortcut = any("shortcut" in s.lower() for s in reasoning_trace)
        contradict = any(
            "not " in s.lower() and " earlier" in s.lower() for s in reasoning_trace
        )
        issues = []
        if circ:
            issues.append("possible circularity")
        if shortcut:
            issues.append("shortcut detected")
        if contradict:
            issues.append("contradiction in trace")
        conf = max(0.3, 1.0 - 0.2 * len(issues))
        advice = []
        if circ:
            advice.append("Add independent evidence or alternative paths.")
        if shortcut:
            advice.append("Expand steps with explicit checks and counterexamples.")
        if contradict:
            advice.append("Reconcile conflicting statements with sources.")
        return {
            "critique": ("; ".join(issues) if issues else "sound reasoning"),
            "confidence": round(conf, 3),
            "advice": advice,
        }
