from __future__ import annotations
import json, time
from pathlib import Path
from typing import List, Dict, Any
from javu_agi.arena.task_bank import (
    append_hard_cases,
    build_training_batch,
    save_to_bank,
)
from javu_agi.eval.eval_harness import (
    run_transfer_set,
    run_adversarial_set,
)  # asumsi ada runner ini
from javu_agi.utils.subprocess_safe import run_cmd

DATA_DIR = Path("./data")
LOGS = Path("./logs")
LOGS.mkdir(parents=True, exist_ok=True)

GATES = {"arena_target": 0.60, "transfer_target": 0.80, "adversarial_target": 0.90}

# earlier code remains
batch = build_training_batch(total=500)
Path("tmp_batch.jsonl").write_text(
        "\n".join(json.dumps(x, ensure_ascii=False) for x in batch), encoding="utf-8"
    )
    # 1) jalankan arena via script eksternal (sinkron)
    # asumsi ./scripts/run_arena.sh menghasilkan logs/arena_report.json
result = run_cmd(["./scripts/run_arena.sh", "500"], timeout=300)
if not result.get("ok"):
        # log already handled by helper; continue with fallback
        pass

def collect_failures(arena_report_path: Path) -> List[Dict[str, Any]]:
    fails = []
    if arena_report_path.is_file():
        rep = json.loads(arena_report_path.read_text())
        for r in rep.get("results", []):
            if not r.get("pass"):
                fails.append(
                    {
                        "task": r["task"],
                        "category": r.get("category", "unknown"),
                        "difficulty": "hard",
                    }
                )
    return fails


def train_cycle_once():
    """
    1) Sample batch -> run arena (pakai skrip lo), simpan report JSON di logs/
    2) Hard-case harvest -> append_hard_cases
    3) Transfer & adversarial eval
    4) Keputusan: bila < target, adjust kurikulum & trigger retrain ringan (opsional)
    """
    batch = build_training_batch(total=500)
    Path("tmp_batch.jsonl").write_text(
        "\n".join(json.dumps(x, ensure_ascii=False) for x in batch), encoding="utf-8"
    )

    # 1) jalankan arena via script eksternal (sinkron)
    # asumsi ./scripts/run_arena.sh menghasilkan logs/arena_report.json
    # (kalau belum, modif script itu untuk output JSON ringkas)
    import subprocess

    subprocess.run(["./scripts/run_arena.sh", "500"], check=False)

    # 2) harvest
    arena_report = LOGS / "arena_report.json"
    fails = collect_failures(arena_report)
    if fails:
        append_hard_cases(fails)

    # 3) eval
    transfer = run_transfer_set()  # return {"acc": float, ...}
    adv = run_adversarial_set()  # return {"pass_rate": float, ...}

    # 4) keputusan & optional retrain
    need_push = (transfer.get("acc", 0.0) < GATES["transfer_target"]) or (
        adv.get("pass_rate", 0.0) < GATES["adversarial_target"]
    )
    (LOGS / "cycle_summary.json").write_text(
        json.dumps(
            {
                "transfer": transfer,
                "adversarial": adv,
                "hard_cases_added": len(fails),
                "ts": int(time.time()),
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    if need_push:
        # di sini letakkan trigger fine-tune ringan / parameter update router / prompt policy
        # contoh: naikkan porsi hard & transfer
        save_to_bank(
            [
                {
                    "task": "AUTO: increase transfer/new domains",
                    "category": "meta",
                    "difficulty": "medium",
                }
            ],
            "auto_notes.jsonl",
        )
    return {"hard_added": len(fails), "transfer": transfer, "adversarial": adv}


def train_cycle_once(*a, **k):
    raise RuntimeError("training disabled: builder OFF")
