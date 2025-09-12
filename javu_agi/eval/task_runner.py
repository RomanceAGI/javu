from __future__ import annotations
from typing import Dict, Any
from javu_agi.eval.eval_harness import EvalHarness
from javu_agi.executive_controller import ExecutiveController

EXEC = ExecutiveController()


def _run(user: str, text: str) -> Dict[str, Any]:
    resp, meta = EXEC.process(user, text)
    return {"response": resp, "meta": meta}


def run_suite(limit_per_file: int | None = 25) -> Dict[str, Any]:
    H = EvalHarness(_run)
    paths = [
        "javu_agi/eval/datasets/wm_span.jsonl",
        "javu_agi/eval/datasets/counterfactual.jsonl",
        "javu_agi/eval/datasets/skill_transfer.jsonl",
    ]
    report = {}
    for p in paths:
        report[p] = H.evaluate_file("evalbot", p, limit=limit_per_file)
    return report


if __name__ == "__main__":
    import json

    print(json.dumps(run_suite(10), indent=2))
