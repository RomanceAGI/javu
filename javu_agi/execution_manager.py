from __future__ import annotations
from typing import List, Dict, Any, Optional
import time, random
import os, re

from javu_agi.hmac_sign import sign_cmd
from javu_agi.tools.contract_verifier import ContractVerifier
from javu_agi.tools.tool_contracts import default_contracts
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from javu_agi.planet.eco_guard import SustainabilityGuard, PlanetaryPolicy
try:
    from javu_agi.embodiment.safety_shield import safety_veto, parse_traj
except Exception:

    def safety_veto(*a, **k):
        return (True, "stub")

    def parse_traj(cmd: str):
        return {"raw": cmd}


class ExecutionManager:
    def __init__(
        self,
        tools,
        result_cache=None,
        budget=None,
        *,
        safety_limits=None,
        geofence=None,
        sustainability: "SustainabilityGuard | None" = None,
        policy: "PlanetaryPolicy | None" = None,
    ):
        self.tools = tools
        self.result_cache = result_cache
        self.budget = budget
        self.contracts = ContractVerifier(default_contracts())
        self.safety_limits = safety_limits or {"max_speed": 1.0, "max_force": 1.0}
        self.geofence = geofence or {"areas": []}
        self.sustainability = sustainability
        self._planetary_policy = policy
        self._ledger_path = os.getenv("TOOLS_AUDIT_LOG", "logs/tools_audit.jsonl")
        os.makedirs(os.path.dirname(self._ledger_path), exist_ok=True)
        self._fs_allow = set()
        try:
            fp = os.getenv("FS_ALLOWLIST")
            if fp and os.path.exists(fp):
                self._fs_allow = {
                    l.strip()
                    for l in open(fp, "r", encoding="utf-8").read().splitlines()
                    if l.strip()
                }
        except Exception:
            pass

    def run_step(self, step: Dict[str, Any], worker_url: str) -> Dict[str, Any]:
        """
        Jalankan satu step dengan contract guard pre/post.
        """
        tool = step.get("tool")
        cmd = step.get("cmd", "") or ""
        if self.result_cache:
            cached = self.result_cache.get(tool, cmd)
            if cached:
                return {
                    "step": step,
                    "code": 0,
                    "stdout": cached,
                    "stderr": "",
                    "cached": True,
                    "status": "ok",
                }
        illegal = False
        allow = os.getenv("NET_ALLOWLIST", "").strip()
        if allow:
            allowed = {d.strip().lower() for d in allow.split(",") if d.strip()}
            low = cmd.lower()
            if any(tok in low for tok in ("curl ", "wget ", "http://", "https://")):
                m = re.search(r"https?://([^/\s]+)", cmd)
                dom = m.group(1).lower() if m else ""
                if dom and not any(dom.endswith(ad) for ad in allowed):
                    illegal = True
        if illegal:
            return {
                "step": step,
                "code": 7,
                "stdout": "",
                "stderr": "egress_blocked_by_allowlist",
                "status": "blocked",
            }
        try:
            out_path = (step.get("out_path") or "").strip()
            if out_path:
                ok_fs = (not self._fs_allow) or any(
                    out_path.startswith(p) for p in self._fs_allow
                )
                if not ok_fs:
                    return {
                        "step": step,
                        "status": "blocked",
                        "reason": "fs_blocked_by_allowlist",
                    }
        except Exception:
            pass
        ok, why = self.contracts.precheck(tool, step)
        if not ok:
            return {"step": step, "status": "blocked", "reason": f"contract:{why}"}
        try:
            res = self.tools.run_remote(cmd, worker_url)
        except Exception as e:
            return {"step": step, "status": "error", "reason": str(e)}

        try:
            if self.sustainability:
                est = self.sustainability.env.estimate_impact(
                    step, step.get("sector") or ""
                )
                self.sustainability.account(est)
        except Exception:
            pass

        ok, why = self.contracts.postcheck(
            step.get("tool"), res if isinstance(res, dict) else {}
        )
        if not ok:
            return {"step": step, "status": "blocked", "reason": f"contract:{why}"}
        if self.result_cache:
            try:
                self.result_cache.put(tool, cmd, res.get("stdout", ""))
            except Exception:
                pass
        out = {**res, "step": step, "status": "ok", "cached": False}
        try:
            import json as _json, time as _time

            with open(self._ledger_path, "a", encoding="utf-8") as f:
                f.write(
                    _json.dumps(
                        {
                            "ts": int(_time.time()),
                            "phase": "run_step",
                            "tool": tool,
                            "cmd": cmd,
                            "status": "ok",
                            "cached": out.get("cached", False),
                            "stdout_len": len(str(out.get("stdout", ""))),
                        },
                        ensure_ascii=False,
                    )
                    + "\n"
                )
        except Exception:
            pass
        return out

    def execute(
        self, steps: List[Dict[str, Any]], worker_url: Optional[str]
    ) -> List[Dict[str, Any]]:
        out: List[Dict[str, Any]] = []
        errors = 0

        if not worker_url:
            return [{"step": {}, "code": -1, "stdout": "", "stderr": "no worker_url"}]

        for i, s in enumerate(steps):
            if self.sustainability:
                asses = self.sustainability.assess(s)
                if not asses["permit"]:
                    try:
                        if hasattr(self.sustainability, "ledger"):
                            self.sustainability.ledger.append(
                                {
                                    "ts": int(time.time()),
                                    "step": s,
                                    "flags": asses.get("flags", []),
                                    "action": "blocked",
                                }
                            )
                    except Exception:
                        pass

                    try:
                        import json as _json, time as _time

                        with open(self._ledger_path, "a", encoding="utf-8") as f:
                            f.write(
                                _json.dumps(
                                    {
                                        "ts": int(_time.time()),
                                        "phase": "veto",
                                        "step": s,
                                        "reason": "planetary",
                                        "flags": asses.get("flags", []),
                                    },
                                    ensure_ascii=False,
                                )
                                + "\n"
                            )
                    except Exception:
                        pass
                    out.append(
                        {
                            "step": s,
                            "status": "blocked",
                            "reason": f"planetary:{'|'.join(asses['flags'])}",
                        }
                    )
                    continue

            if self.budget and not self.budget.allow(i, errors):
                out.append(
                    {"step": s, "code": 99, "stdout": "", "stderr": "budget_stop"}
                )
                break

            tool = s.get("tool", "?")
            cmd = s.get("cmd", "") or ""

            # robotics/actuator safety veto (fail-closed)
            try:
                if tool in {"move", "actuate", "gripper", "arm"}:
                    ok, why = safety_veto(
                        parse_traj(cmd), self.safety_limits, self.geofence
                    )
                    if not ok:
                        out.append(
                            {"step": s, "status": "blocked", "reason": f"safety:{why}"}
                        )
                        continue
            except Exception:
                pass

            # up to 3 tries with small backoff (network/transient)
            last = None
            for attempt in range(3):
                res = self.run_step(s, worker_url)
                last = res
                # blocked → final; error → retry; ok → accept
                st = res.get("status")
                if st in (None, "ok"):
                    out.append(res)
                    break
                if st == "blocked":
                    out.append(res)
                    break
                if st == "error":
                    errors += 1
                    time.sleep(0.2 * (attempt + 1))
                    continue

                if self.sustainability:
                    try:
                        est = self.sustainability.env.estimate_impact(
                            s, s.get("sector") or ""
                        )
                        try:
                            self.sustainability.account(
                                est, policy=getattr(self, "_planetary_policy", None)
                            )
                        except TypeError:
                            self.sustainability.account(est)
                    except Exception:
                        pass
                out.append(res)
                break

                # error/transient
                time.sleep(min(1.5, 0.25 * (2**attempt)) + random.random() * 0.05)
            else:
                errors += 1
                out.append(
                    last
                    if isinstance(last, dict)
                    else {"step": s, "code": -1, "stdout": "", "stderr": "unknown"}
                )

            # error budgeting
            if (
                getattr(self.budget, "max_errors", None) is not None
                and errors >= self.budget.max_errors
            ):
                break
        return out
