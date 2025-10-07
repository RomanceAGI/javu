from __future__ import annotations
from dataclasses import dataclass
import os
from typing import Dict, Any


@dataclass
class PlanetaryPolicy:
    max_co2e_day: float
    max_water_m3_day: float
    biodiversity_veto: bool
    social_risk_max: float
    sector_caps: Dict[str, Dict[str, float]]

    @classmethod
    def from_path(cls, path: str) -> "PlanetaryPolicy":
        import os, json

        cfg = {}
        try:
            if path.endswith(".yaml") or path.endswith(".yml"):
                import yaml  # type: ignore

                with open(path, "r", encoding="utf-8") as f:
                    cfg = yaml.safe_load(f) or {}
            else:
                with open(path, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
        except Exception:
            cfg = {}
        return cls(
            max_co2e_day=float(
                cfg.get("max_co2e_day", os.getenv("PLANETARY_MAX_CO2E_DAY", "2000"))
            ),  # kg
            max_water_m3_day=float(
                cfg.get(
                    "max_water_m3_day", os.getenv("PLANETARY_MAX_WATER_M3_DAY", "500")
                )
            ),
            biodiversity_veto=str(
                cfg.get("biodiversity_veto", os.getenv("BIODIVERSITY_VETO", "1"))
            ).lower()
            in {"1", "true", "yes"},
            social_risk_max=float(
                cfg.get("social_risk_max", os.getenv("SOCIAL_RISK_MAX", "0.6"))
            ),
            sector_caps=cfg.get("sector_caps", {}),
        )


class EnvDataAdapter:
    """Heuristik aman; ganti dengan provider nyata (LCA/EF DB) kalau tersedia."""

    def estimate_impact(self, step: Dict[str, Any], sector: str) -> Dict[str, float]:
        cmd = (step.get("cmd") or "").lower()
        co2e_kg = 0.0
        water_m3 = 0.0
        biodiversity_risk = 0.1
        social_risk = 0.1
        if sector == "agriculture":
            if "apply_fertilizer" in cmd:
                co2e_kg += 120
                water_m3 += 2
                biodiversity_risk = max(biodiversity_risk, 0.4)
            if "irrigat" in cmd:
                water_m3 += 10
            if "till" in cmd:
                co2e_kg += 50
                biodiversity_risk = max(biodiversity_risk, 0.5)
        elif sector == "oil_gas":
            if "drill" in cmd:
                co2e_kg += 500
                water_m3 += 30
                biodiversity_risk = max(biodiversity_risk, 0.6)
                social_risk = max(social_risk, 0.5)
            if "flare" in cmd:
                co2e_kg += 800
                biodiversity_risk = max(biodiversity_risk, 0.7)
            if "methane_leak_check" in cmd:
                co2e_kg -= 50
        elif sector == "infrastructure":
            if "pour_concrete" in cmd:
                co2e_kg += 350
                water_m3 += 5
            if "route_plan" in cmd and "avoid_wetland" in cmd:
                biodiversity_risk = max(0.0, biodiversity_risk - 0.2)
        return {
            "co2e_kg": max(0.0, co2e_kg),
            "water_m3": max(0.0, water_m3),
            "biodiversity_risk": max(0.0, min(1.0, biodiversity_risk)),
            "social_risk": max(0.0, min(1.0, social_risk)),
        }


class SustainabilityGuard:
    def __init__(
        self,
        policy: PlanetaryPolicy,
        env_adapter: EnvDataAdapter | None = None,
        ledger: Dict[str, float] | None = None,
    ):
        self.policy = policy
        self.env = env_adapter or EnvDataAdapter()
        self.ledger = ledger or {}  # {"co2e_day_kg": float, "water_day_m3": float}
        self.ledger_path = os.getenv("PLANET_LEDGER", "logs/planet_ledger.json")
        self._rollover_if_needed()

    def _infer_sector(self, step: Dict[str, Any]) -> str:
        t = (
            (step.get("sector") or "")
            + " "
            + (step.get("tool") or "")
            + " "
            + (step.get("cmd") or "")
        ).lower()
        if any(
            k in t for k in ("fertil", "irrigat", "soil", "crop", "seeding", "harvest")
        ):
            return "agriculture"
        if any(
            k in t for k in ("drill", "rig", "pipeline", "well", "flare", "methane")
        ):
            return "oil_gas"
        if any(
            k in t
            for k in ("concrete", "cement", "rebar", "bridge", "rail", "highway", "dam")
        ):
            return "infrastructure"
        return "general"

    def assess(self, step: Dict[str, Any]) -> Dict[str, Any]:
        sector = step.get("sector") or self._infer_sector(step)
        est = self.env.estimate_impact(step, sector)
        flags: list[str] = []

        cap = self.policy.sector_caps.get(sector, {})
        if est["co2e_kg"] / 1000.0 > float(cap.get("co2e_t_limit", float("inf"))):
            flags.append("co2e_sector_cap")
        if est["water_m3"] > float(cap.get("water_m3_limit", float("inf"))):
            flags.append("water_sector_cap")
        if self.policy.biodiversity_veto and est["biodiversity_risk"] > 0.6:
            flags.append("biodiversity_veto")
        if est["social_risk"] > self.policy.social_risk_max:
            flags.append("social_risk")

        if (
            self.ledger.get("co2e_day_kg", 0.0) + est["co2e_kg"]
            > self.policy.max_co2e_day
        ):
            flags.append("co2e_day_budget")
        if (
            self.ledger.get("water_day_m3", 0.0) + est["water_m3"]
            > self.policy.max_water_m3_day
        ):
            flags.append("water_day_budget")
        out = {
            "sector": sector,
            "estimate": est,
            "flags": flags,
            "permit": len(flags) == 0,
        }
        return out

    def permit_step(self, step: Dict[str, Any]) -> bool:
        return self.assess(step)["permit"]

    def account(self, est: Dict[str, Any]) -> None:
        self.ledger["co2e_day_kg"] = self.ledger.get("co2e_day_kg", 0.0) + est.get(
            "co2e_kg", 0.0
        )
        self.ledger["water_day_m3"] = self.ledger.get("water_day_m3", 0.0) + est.get(
            "water_m3", 0.0
        )
        # persist + audit (best-effort)
        try:
            import json, time

            with open(self.ledger_path, "w", encoding="utf-8") as f:
                json.dump(self.ledger, f)
            from javu_agi.audit.audit_chain import AuditChain

            AuditChain(log_dir=os.getenv("AUDIT_CHAIN_DIR", "logs/audit_chain")).commit(
                "planetary_account",
                {
                    "co2e_day_kg": self.ledger.get("co2e_day_kg", 0.0),
                    "water_day_m3": self.ledger.get("water_day_m3", 0.0),
                },
            )
        except Exception:
            pass

    # Helpers
    def _rollover_if_needed(self) -> None:
        try:
            import json, datetime

            today = datetime.date.today().isoformat()
            meta_path = self.ledger_path + ".meta"
            last = {}
            if os.path.exists(meta_path):
                last = json.load(open(meta_path, "r"))
            if last.get("day") != today:
                self.ledger["co2e_day_kg"] = 0.0
                self.ledger["water_day_m3"] = 0.0
                json.dump({"day": today}, open(meta_path, "w"))
        except Exception:
            pass
