from dataclasses import dataclass
from typing import Dict, Any, List
import math, statistics as stats


@dataclass
class Policy:
    name: str
    params: Dict[str, float]  # mis. {"tax_rate": 0.12, "subsidy_edu": 0.01}


class PolicySimulator:
    """Micro-sim cepat: proxy indikator (growth, gini, unemployment, edu_index)."""

    def __init__(self, baseline: Dict[str, float]):
        self.base = baseline  # ambil dari data_connect (GDP, Gini, dsb.)

    def score(self, p: Policy) -> Dict[str, float]:
        gdp = self.base["gdp"]
        gini = self.base["gini"]
        unemp = self.base["unemployment"]
        edu = self.base["edu_index"]

        tr = p.params.get("tax_rate", 0.1)
        sub_edu = p.params.get("subsidy_edu", 0.0)
        health = p.params.get("health_spend", 0.0)

        # proxy sederhana: (pakai fungsi halus agar monotonic dan bounded)
        growth = (1 - 0.5 * tr) + 0.2 * sub_edu + 0.1 * health
        growth = max(-0.1, min(0.12, growth))  # -10% .. +12%

        new_gdp = gdp * (1 + growth)
        new_gini = max(0.20, min(0.70, gini - 0.3 * sub_edu + 0.05 * tr))
        new_unemp = max(0.01, min(0.35, unemp - 0.2 * growth + 0.05 * tr))
        new_edu = max(0.1, min(0.95, edu + 0.5 * sub_edu))

        # utility agregat (pareto-ish)
        welfare = (
            math.log(new_gdp + 1)
            - 0.5 * new_gini
            + 0.2 * (1 - new_unemp)
            + 0.3 * new_edu
        )
        return {
            "gdp": new_gdp,
            "gini": new_gini,
            "unemployment": new_unemp,
            "edu_index": new_edu,
            "welfare": welfare,
            "growth": growth,
        }

    def compare(self, policies: List[Policy]) -> Dict[str, Any]:
        out = []
        for p in policies:
            s = self.score(p)
            s["policy"] = p.name
            s["params"] = p.params
            out.append(s)
        out = sorted(out, key=lambda x: x["welfare"], reverse=True)
        return {"ranked": out, "best": out[0] if out else None}
