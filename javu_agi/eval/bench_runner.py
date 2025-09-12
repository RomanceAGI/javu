from __future__ import annotations
import json, re, sys, time
from pathlib import Path
from typing import Dict, Any, List
from javu_agi.executive_controller import ExecutiveController


def _check(rule: Dict[str, Any], text: str) -> bool:
    t = text or ""
    kind = rule.get("check", "contains")
    val = str(rule.get("value", ""))
    if kind == "contains":
        return val.lower() in t.lower()
    if kind == "equals":
        return t.strip().lower() == val.strip().lower()
    if kind == "regex":
        try:
            return re.search(val, t, re.I) is not None
        except re.error:
            return False
    return False


def run_file(path: str, limit: int | None = None) -> Dict[str, Any]:
    items: List[Dict[str, Any]] = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        items.append(json.loads(line))
    if limit:
        items = items[:limit]

    execu = ExecutiveController()
    t0 = time.time()
    rows = []
    for i, it in enumerate(items, 1):
        prm = it.get("prompt", "")
        rule = it.get("rule") or {"check": "contains", "value": it.get("answer", "")}
        out, meta = execu.process(user_id="bench", prompt=prm)
        ok = _check(rule, out)
        rows.append(
            {
                "i": i,
                "ok": ok,
                "latency": meta.get("latency_s", 0),
                "reward": meta.get("reward", 0.0),
                "conf": meta.get("chosen_confidence", 0.0),
                "risk": meta.get("chosen_risk", "low"),
            }
        )
    dt = round(time.time() - t0, 2)
    acc = round(sum(1 for r in rows if r["ok"]) / max(1, len(rows)), 4)
    return {
        "n": len(rows),
        "acc": acc,
        "elapsed_s": dt,
        "avg_latency": round(sum(r["latency"] for r in rows) / max(1, len(rows)), 3),
        "avg_reward": round(sum(r["reward"] for r in rows) / max(1, len(rows)), 3),
        "avg_conf": round(sum(r["conf"] for r in rows) / max(1, len(rows)), 3),
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m javu_agi.eval.bench_runner <dataset.jsonl> [limit]")
        sys.exit(2)
    path = sys.argv[1]
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else None
    res = run_file(path, limit=limit)
    print(json.dumps(res, indent=2))
