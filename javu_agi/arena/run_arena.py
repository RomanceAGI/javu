from __future__ import annotations
from typing import Dict, Any, List
from pathlib import Path
import random, time, json

from javu_agi.arena.task_bank import sample_mix
from javu_agi.learn.curriculum import build_default_curriculum, Sampler, Task
from javu_agi.learn.curriculum_bank import save_to_bank
from javu_agi.executive_controller import ExecutiveController
from javu_agi.arena.checker import duel


def run_arena(
    rounds: int = 200,
    seed: int = 7,
    outdir: str = "data/arena",
    use_bank: bool = True,
    bank_name: str = "auto_hard.jsonl",
) -> Dict[str, Any]:
    random.seed(seed)
    execu = ExecutiveController()
    cur = build_default_curriculum()
    samp = Sampler(cur, stage=0, batch=8)
    Path(outdir).mkdir(parents=True, exist_ok=True)
    stats = {"S2": 0, "S3": 0, "ties": 0, "stage": 0, "rounds": 0}
    t0 = time.time()

    for r in range(rounds):
        batch: List[Task] = samp.next_batch()
        if use_bank:
            try:
                mix = sample_mix(
                    default_sets=["datasets/plan_chain.jsonl"],
                    bank_name=bank_name,
                    k_bank=4,
                    k_each=4,
                )
                batch = batch[:4] + [
                    Task(
                        prompt=m["prompt"],
                        rule=m["rule"],
                        tags=m.get("tags", ["general"]),
                    )
                    for m in mix[:4]
                ]
            except FileNotFoundError:
                pass  # jalan terus tanpa bank

        wins = {"S2": 0, "S3": 0}
        logs = []
        new_hard = []
        for t in batch:
            res = duel(execu, t.prompt, t.rule, modes=("S2", "S3"))
            wins[res.get("winner", "S2")] += 1
            ok = res.get("winner") in ("S2", "S3")
            if not ok:
                new_hard.append(
                    {
                        "prompt": t.prompt,
                        "rule": t.rule,
                        "tags": t.tags,
                        "source": {"arena_round": r},
                    }
                )
            logs.append(
                {"prompt": t.prompt, "rule": t.rule, "winner": res.get("winner", "")}
            )

        if new_hard:
            save_to_bank(new_hard, bank_name=bank_name)

        if wins["S3"] >= max(1, len(batch) // 2):
            samp.harder()
            stats["stage"] = samp.stage
        elif wins["S2"] >= max(1, len(batch) // 2) and samp.stage > 0:
            samp.easier()
            stats["stage"] = samp.stage

        stats["S2"] += wins["S2"]
        stats["S3"] += wins["S3"]
        stats["rounds"] += 1
        Path(outdir, f"arena_round_{r:04d}.json").write_text(
            json.dumps({"wins": wins, "logs": logs}, indent=2), encoding="utf-8"
        )

    stats["elapsed_s"] = round(time.time() - t0, 2)
    Path(outdir, f"summary_{int(t0)}.json").write_text(
        json.dumps(stats, indent=2), encoding="utf-8"
    )
    return stats


def run_arena(*a, **k):
    raise RuntimeError("arena builder disabled: no hard-case dataset generation")


def main(*a, **k):
    raise RuntimeError("arena builder disabled: no hard-case dataset generation")
