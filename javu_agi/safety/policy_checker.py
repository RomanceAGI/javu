"""
Minimal, auditable policy checker.

Design goals:
- Deny-by-default for high-risk actions.
- Return structured verdict with reasons & severity.
- Easy to extend with org-specific rules.
"""
from __future__ import annotations
import re
from typing import Dict, Any, List
from javu_agi.utils.logging_config import get_logger, redact

logger = get_logger("javu_agi.safety.policy_checker")

# Example deny patterns (conservative). Extend per policy.
DENY_PATTERNS = [
    (re.compile(r"\b(ddos|dos|denial of service)\b", re.I), "malicious_network", "high"),
    (re.compile(r"\b(private key|api[_-]?key|secret|password)\b", re.I), "secrets_exfil", "high"),
    (re.compile(r"\b(exploit|zero[- ]day|privilege escalation)\b", re.I), "exploit_instructions", "high"),
    (re.compile(r"\b(bypass|evade|disable).*(audit|sandbox|monitor)", re.I), "evasion", "high"),
    (re.compile(r"\b(personal data|pii|ssn|passport|credit card)\b", re.I), "pii_handling", "high"),
    (re.compile(r"\b(rewrite policy|delete audit|disable logging)\b", re.I), "tamper_audit", "high"),
]

LOWER_RISK_PATTERNS = [
    (re.compile(r"\b(scrape|bulk download)\b", re.I), "data_collection", "medium"),
    (re.compile(r"\b(automate email|autodial)\b", re.I), "communication_automation", "medium"),
]


def evaluate_request(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Evaluate incoming planned action or prompt.
    payload: {"actor": "...", "cmd": "...", "context": {...}}
    Returns: {"ok": bool, "allow": bool, "reasons": [...], "max_severity": "low|medium|high"}
    """
    try:
        txt = " ".join(
            str(payload.get(k, "")) for k in ("cmd", "prompt", "goal", "description")
        )
        txt = txt.lower()
        reasons: List[Dict[str, str]] = []
        max_sev = "low"
        # Check deny patterns
        for pat, code, sev in DENY_PATTERNS:
            if pat.search(txt):
                reasons.append({"code": code, "pattern": pat.pattern, "severity": sev})
                if sev == "high":
                    max_sev = "high"
        for pat, code, sev in LOWER_RISK_PATTERNS:
            if pat.search(txt):
                reasons.append({"code": code, "pattern": pat.pattern, "severity": sev})
                if max_sev != "high" and sev == "medium":
                    max_sev = "medium"
        allow = len([r for r in reasons if r["severity"] == "high"]) == 0
        result = {"ok": True, "allow": allow, "reasons": reasons, "max_severity": max_sev}
        logger.debug("Policy evaluate: %s -> %s", redact(payload), redact(result))
        return result
    except Exception:
        logger.exception("Policy evaluation failed")
        return {"ok": False, "allow": False, "reasons": [{"code": "eval_error", "severity": "high"}], "max_severity": "high"}