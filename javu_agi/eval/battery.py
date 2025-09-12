from __future__ import annotations
import json, time
from pathlib import Path
from typing import List, Dict, Any
from javu_agi.eval.bench_runner import run_file
from javu_agi.eval.rct_runner import run_rct

SUITES = [
    ("datasets/math_gsm8k_small.jsonl", 200),
    ("datasets/arc_c_small.jsonl", 200),
    ("datasets/code_humaneval_small.jsonl", 164),
    ("datasets/mmlu_science_small.jsonl", 200),
    ("datasets/plan_chain.jsonl", 150),
]


def run_battery(outdir: str = "data/eval"):
    Path(outdir).mkdir(parents=True, exist_ok=True)
    allres: Dict[str, Any] = {"suites": {}, "ts": int(time.time())}
    for path, limit in SUITES:
        if not Path(path).exists():
            continue
        res = run_file(path, limit=limit)
        allres["suites"][Path(path).name] = res
    # RCT uplift contextual vs non-contextual
    qs = []
    for path, limit in SUITES:
        if Path(path).exists():
            for line in (
                Path(path).read_text(encoding="utf-8").splitlines()[: min(limit, 100)]
            ):
                j = json.loads(line)
                qs.append(j.get("prompt", ""))
    if qs:
        allres["rct"] = run_rct(qs, per_arm=min(40, len(qs) // 2))
    out = Path(outdir) / f"battery_{allres['ts']}.json"
    out.write_text(json.dumps(allres, indent=2), encoding="utf-8")
    return str(out)


if __name__ == "__main__":
    print(run_battery())
