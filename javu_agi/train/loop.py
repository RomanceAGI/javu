from __future__ import annotations
import json, time, os
from pathlib import Path
from typing import Dict, Any
from javu_agi.arena.runner import run_arena
from javu_agi.learn.curriculum_gen import generate as mine_hard
from javu_agi.eval.battery import run_battery
from javu_agi.memory.memory_manager import MemoryManager

OUT = Path("data/train")
OUT.mkdir(parents=True, exist_ok=True)


def _write(obj: Dict[str, Any], name: str):
    p = OUT / f"{name}_{int(time.time())}.json"
    p.write_text(json.dumps(obj, indent=2), encoding="utf-8")
    return str(p)


def epoch(ep: int, rounds: int = 150) -> Dict[str, Any]:
    t0 = time.time()
    # 1) self-play arena (pakai bank hard cases juga)
    arena_res = run_arena(rounds=rounds, use_bank=True, bank_name="auto_hard.jsonl")
    # 2) mine hard cases baru dari trace → task bank
    mined = mine_hard(limit_sweep=1000, bank_name="auto_hard.jsonl")
    # 3) battery eval (GSM/ARC/MMLU/Code/Plan subset)
    battery_path = run_battery(outdir="data/eval")
    # 4) konsolidasi memory sekali ekstra di akhir epoch
    try:
        mm = MemoryManager()
        cons = mm.consolidate()
    except Exception as e:
        cons = {"error": str(e)}
    dt = round(time.time() - t0, 2)
    return {
        "epoch": ep,
        "elapsed_s": dt,
        "arena": arena_res,
        "mined": mined,
        "battery": battery_path,
        "consolidation": cons,
    }


def run(epochs: int = 5, rounds_per_epoch: int = 150):
    logs = []
    for ep in range(1, epochs + 1):
        res = epoch(ep, rounds=rounds_per_epoch)
        logs.append(res)
        _write(res, f"epoch_{ep}")
    _write({"summary": logs}, "train_summary")
    return logs


if __name__ == "__main__":
    E = int(os.getenv("EPOCHS", "3"))
    R = int(os.getenv("ROUNDS", "120"))
    print(json.dumps(run(E, R), indent=2))


def main(*a, **k):
    raise RuntimeError("training disabled: builder OFF")
