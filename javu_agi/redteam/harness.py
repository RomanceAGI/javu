"""
Red-team harness that runs tests only in simulation mode.

- No network, no subprocess, no file mutations outside tmp/.
- Tests are structured scenarios that the system should refuse or escalate.

Use run_simulation() to execute red-team scenarios safely.
"""
from __future__ import annotations
import tempfile
import shutil
import os
from typing import List, Dict, Any
from javu_agi.utils.logging_config import get_logger

logger = get_logger("javu_agi.redteam.harness")


def run_simulation(scenarios: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    results = []
    tmp = tempfile.mkdtemp(prefix="javu_redteam_")
    try:
        for s in scenarios:
            # Simulate evaluation without executing external commands or network calls.
            # For each scenario we call policy/eval functions and capture the verdict.
            try:
                # simple heuristic: call policy_checker if available
                from javu_agi.safety.policy_checker import evaluate_request
                verdict = evaluate_request(s.get("action", {}))
            except Exception:
                verdict = {"ok": False, "allow": False, "reasons": [{"code": "sim_error"}], "max_severity": "high"}
            res = {"scenario": s.get("name", "<unnamed>"), "verdict": verdict}
            logger.debug("Redteam simulate: %s -> %s", s.get("name"), verdict)
            results.append(res)
        return results
    finally:
        try:
            shutil.rmtree(tmp)
        except Exception:
            pass