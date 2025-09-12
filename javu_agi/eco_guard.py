from __future__ import annotations
import os, re
from typing import Any, Dict

_HARD = re.compile(
    r"\b(nuke|ddos|leak|exploit|poison|weapon|kill|harm|pollute|toxic|bio|radiation)\b",
    re.I,
)
_ENERGY = re.compile(
    r"\b(gpu farm|mine crypto|mining|proof[- ]of[- ]work|render farm|brute[- ]force)\b",
    re.I,
)
_ENV = re.compile(
    r"\b(deforest|burning|incinerat|dump|waste|oil spill|coal|diesel|plastic burn|landfill)\b",
    re.I,
)


class EcoGuard:
    def __init__(self) -> None:
        self.max_risk = float(os.getenv("ECO_MAX_RISK", "0.35"))
        self.max_energy = float(os.getenv("ECO_MAX_ENERGY", "0.7"))
        self.max_env = float(os.getenv("ECO_MAX_ENV", "0.5"))
        self.block_on_energy = os.getenv("ECO_BLOCK_ON_ENERGY", "1") in {
            "1",
            "true",
            "yes",
        }
        self.block_on_env = os.getenv("ECO_BLOCK_ON_ENV", "1") in {"1", "true", "yes"}
        self.last: Dict[str, Any] = {}

    def score(
        self, task: str, plan: str = "", meta: Dict[str, Any] | None = None
    ) -> Dict[str, Any]:
        s_hard = 1.0 if _HARD.search(text) else 0.0
        s_energy = 0.7 if _ENERGY.search(text) else 0.05
        s_env = 0.7 if _ENV.search(text) else 0.05
        risk = max(s_hard, (s_energy + s_env) / 2.0)
        allow = (
            (risk <= self.max_risk)
            and (s_energy <= self.max_energy)
            and (s_env <= self.max_env)
        )
        flags = []
        if s_hard >= 1.0:
            flags.append("hard_risk")
        if s_energy > self.max_energy and self.block_on_energy:
            flags.append("energy_high")
        if s_env > self.max_env and self.block_on_env:
            flags.append("env_high")
        if risk > self.max_risk:
            flags.append("risk_over_cap")
        allow = len(flags) == 0
        self.last = {"risk": risk, "energy": s_energy, "env": s_env, "allow": allow}
        return dict(self.last)

    def enforce(
        self, task: str, plan: str = "", meta: Dict[str, Any] | None = None
    ) -> None:
        r = self.score(task=task, plan=plan, meta=meta)
        if not r["allow"]:
            try:
                from javu_agi.audit.audit_chain import AuditChain

                AuditChain(
                    log_dir=os.getenv("AUDIT_CHAIN_DIR", "logs/audit_chain")
                ).commit(
                    "eco_guard_block", {"risk": r["risk"], "flags": r.get("flags", [])}
                )
            except Exception:
                pass
            raise RuntimeError("eco guard blocked request")

    @staticmethod
    def infer_sector(text: str) -> str:
        t = text.lower()
        if any(k in t for k in ("fertil", "irrigat", "soil", "crop", "harvest")):
            return "agriculture"
        if any(k in t for k in ("drill", "rig", "pipeline", "flare", "methane")):
            return "oil_gas"
        if any(
            k in t
            for k in ("concrete", "cement", "rebar", "bridge", "rail", "dam", "highway")
        ):
            return "infrastructure"
        return "general"
