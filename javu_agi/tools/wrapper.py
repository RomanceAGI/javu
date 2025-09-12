from __future__ import annotations
import os, time, json, re
from typing import Any, Callable, Dict, Optional, Tuple, List

# ---- global governance hooks (already in your codebase) ----
try:
    from javu_agi.audit_chain import AuditChain
except Exception:  # fallback if import path differs

    class AuditChain:
        def __init__(self, log_dir="logs/audit_chain"):
            os.makedirs(log_dir, exist_ok=True)

        def commit(self, kind: str, record: Dict[str, Any]):
            return {"kind": kind, "ts": int(time.time()), "ok": True}


try:
    from javu_agi.governance.ethics_gate import EthicsGate
    from javu_agi.planet.sustainability_guard import SustainabilityGuard
    from javu_agi.security.privacy_guard import PrivacyGuard
except Exception:

    class _Null:
        def check(self, *_a, **_k):
            return {"permit": True, "flags": []}

    EthicsGate = SustainabilityGuard = PrivacyGuard = _Null

AUDIT = AuditChain(log_dir=os.getenv("AUDIT_CHAIN_DIR", "logs/audit_chain"))
QUALITY_LOG = os.getenv("QUALITY_LOG", "logs/quality.jsonl")
os.makedirs(os.path.dirname(QUALITY_LOG), exist_ok=True)

# ---- global denylist & URL/domain guards ----
_DENY = {
    "judi",
    "phishing",
    "carding",
    "deepfake",
    "scam",
    "ransomware",
    "keylogger",
    "child sexual",
    "cp ",
    "terror",
    "explosive",
    "credit card dump",
}
_URL_RX = re.compile(r"https?://[^\s]+", re.I)


def _deny_fast(text: str) -> Optional[str]:
    low = (text or "").lower()
    if any(k in low for k in _DENY):
        return "request_blocked_by_policy"
    return None


def _url_allow(text: str) -> bool:
    # allowlist domain via ENV EGRESS_ALLOWLIST (comma separated)
    allow = {
        d.strip() for d in os.getenv("EGRESS_ALLOWLIST", "").split(",") if d.strip()
    }
    if not allow:
        return True
    for u in _URL_RX.findall(text or ""):
        try:
            host = u.split("://", 1)[1].split("/", 1)[0].split("@")[-1].split(":")[0]
            if not any(host.endswith(d) for d in allow):
                return False
        except Exception:
            return False
    return True


def _log_quality(kind: str, score: float, warnings: List[str], meta: Dict[str, Any]):
    row = {
        "ts": int(time.time()),
        "kind": kind,
        "score": float(score),
        "warnings": warnings,
        "meta": meta,
    }
    with open(QUALITY_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


Validator = Callable[[str], Tuple[bool, List[str], Optional[Dict[str, Any]]]]
Scorer = Callable[[str, Optional[Dict[str, Any]]], float]
Executor = Callable[[str], str]


def run_tool(
    name: str,
    executor: Executor,
    user_input: str,
    *,
    validator: Optional[Validator] = None,
    scorer: Optional[Scorer] = None,
    governance: bool = True,
) -> str:
    # fast lexical/policy guards
    deny = _deny_fast(user_input)
    if deny:
        AUDIT.commit(kind=f"{name}:deny", record={"reason": deny})
        return json.dumps({"error": deny})

    if not _url_allow(user_input):
        AUDIT.commit(kind=f"{name}:deny", record={"reason": "egress_not_allowlisted"})
        return json.dumps({"error": "egress_not_allowlisted"})

    # privacy/ethics checks (pre)
    if governance:
        if hasattr(PrivacyGuard, "check") and not PrivacyGuard().check(user_input).get(
            "permit", True
        ):
            AUDIT.commit(kind=f"{name}:deny", record={"reason": "privacy_guard"})
            return json.dumps({"error": "privacy_violation"})
        if hasattr(EthicsGate, "check") and not EthicsGate().check(user_input).get(
            "permit", True
        ):
            AUDIT.commit(kind=f"{name}:deny", record={"reason": "ethics_guard"})
            return json.dumps({"error": "ethics_violation"})

    # execute
    t0 = time.time()
    out = executor(user_input)
    dt = time.time() - t0

    parsed: Optional[Dict[str, Any]] = None
    warns: List[str] = []
    ok = True
    if validator:
        try:
            ok, warns, parsed = validator(out)  # (ok, warnings, parsed_obj)
        except Exception as e:
            ok, warns = False, [f"validator_error:{e}"]

    score = 0.5
    if scorer:
        try:
            score = float(scorer(out, parsed))
        except Exception as e:
            warns.append(f"scorer_error:{e}")

    # sustainability (post) — veto heavy impact if available
    if governance and hasattr(SustainabilityGuard, "assess"):
        assess = SustainabilityGuard().assess({"kind": name, "len": len(out)})
        if not assess.get("permit", True):
            AUDIT.commit(
                kind=f"{name}:veto_planet", record={"flags": assess.get("flags", [])}
            )
            return json.dumps(
                {"error": "planetary_veto", "flags": assess.get("flags", [])}
            )

    # audit & quality log
    AUDIT.commit(
        kind=f"{name}:exec",
        record={
            "ok": ok,
            "score": score,
            "duration_ms": int(dt * 1000),
            "warnings": warns[:8],
            "size": len(out),
        },
    )
    _log_quality(name, score, warns, {"ms": int(dt * 1000), "size": len(out)})

    return out
