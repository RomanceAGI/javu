from __future__ import annotations
from typing import List, Dict, Any

try:
    from javu_agi.causal_reasoning import reason_about_cause as _legacy_cause
except Exception:
    _legacy_cause = None


class LegacyCausalAdapter:
    """
    Adapter untuk menyatukan casual_reasoning (legacy) ke pipeline causal.
    Tidak melakukan training apapun.
    """

    def __init__(self, memory):
        self.memory = memory

    def annotate(
        self, user_id: str, prompt: str, steps: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        if not _legacy_cause:
            return steps
        try:
            note = _legacy_cause(user_id, prompt)  # pakai memory recall dari modul lo
            out = []
            for s in steps:
                ss = dict(s)
                ss["_cause_note"] = note
                out.append(ss)
            return out
        except Exception:
            return steps

    def rerank(self, steps: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Heuristik ringan: jika _cause_note menunjuk masalah strategi, dorong langkah yang lebih 'diagnostic' ke atas.
        """
        if not steps:
            return steps

        def is_diagnostic(cmd: str) -> bool:
            c = (cmd or "").lower()
            return any(
                k in c
                for k in ["check", "verify", "measure", "validate", "probe", "inspect"]
            )

        return sorted(steps, key=lambda z: (not is_diagnostic(z.get("cmd", "")), 0))
