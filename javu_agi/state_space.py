from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Any


@dataclass
class StructuredState:
    facts: Dict[str, Any] = field(
        default_factory=dict
    )  # ex: {"has_csv": True, "url_ok": False}
    goals: Dict[str, Any] = field(
        default_factory=dict
    )  # ex: {"summarize": 0.5} (progress 0..1)
    risks: Dict[str, float] = field(
        default_factory=dict
    )  # ex: {"privacy":0.1,"security":0.2}
    meta: Dict[str, Any] = field(default_factory=dict)  # misc: step, domain, etc.

    def as_text(self) -> str:
        f = " ".join(f"{k}={v}" for k, v in sorted(self.facts.items()))
        g = " ".join(f"{k}:{v:.2f}" for k, v in sorted(self.goals.items()))
        r = " ".join(f"{k}:{v:.2f}" for k, v in sorted(self.risks.items()))
        return f"[FACTS {f}] [GOALS {g}] [RISKS {r}]"

    def update_from_tool(self, tool: str, stdout: str) -> None:
        # Heuristik ringan; bisa diperluas. Jangan agresif (no downgrade).
        s = (stdout or "").lower()
        if "csv" in s:
            self.facts["has_csv"] = True
        if "http/" in s or "status" in s:
            self.facts["http_touched"] = True
        # progress cues
        if "summary" in s or "ringkasan" in s:
            self.goals["summarize"] = max(self.goals.get("summarize", 0.0), 0.6)
