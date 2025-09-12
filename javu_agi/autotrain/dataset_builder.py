import os, json, glob, hashlib
from pathlib import Path
from typing import List, Dict, Any

DISTILL_DIR = Path(os.getenv("DISTILL_DIR", "artifacts/distill"))
OUT_DIR = Path(os.getenv("AUTOTRAIN_OUT", "artifacts/autotrain")) / "datasets"


def _sha1(x: str) -> str:
    import hashlib

    return hashlib.sha1(x.encode()).hexdigest()


def _iter_jsonl(paths: List[str]):
    for p in paths:
        with open(p, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    try:
                        yield json.loads(line)
                    except json.JSONDecodeError:
                        # Skip lines that aren't valid JSON instead of silently
                        # catching everything. Other errors (like I/O) will propagate.
                        continue


def build_sft_dataset(split_ratio: float = 0.98) -> Dict[str, str]:
    """
    Ambil distill logs: input/tool traces/critique/final → jadikan (prompt, response) SFT.
    Return path train.jsonl & val.jsonl
    """
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    files = sorted(glob.glob(str(DISTILL_DIR / "**/*.jsonl"), recursive=True))
    if not files:
        raise RuntimeError(f"No distill logs in {DISTILL_DIR}")

    samples = []
    for ex in _iter_jsonl(files):
        prompt = ex.get("prompt") or ex.get("input") or ""
        answer = ex.get("final") or ex.get("response") or ""
        if not prompt or not answer:
            continue
        # optional: tambahkan reasoning/critique/tool traces sebagai context
        traces = ex.get("traces") or {}
        critique = ex.get("critique") or ""
        sysctx = (
            f"\n\n[TOOLS]\n{json.dumps(traces)[:2000]}\n\n[CRITIQUE]\n{critique[:1000]}"
        )
        samples.append({"prompt": prompt + sysctx, "response": answer})

    if len(samples) < 200:  # minimal awal
        raise RuntimeError(f"Too few distill samples: {len(samples)} (<200)")

    import random

    random.shuffle(samples)
    n = len(samples)
    k = int(n * split_ratio)
    train, val = samples[:k], samples[k:]

    train_p = OUT_DIR / f"sft_train_{_sha1(str(n))}.jsonl"
    val_p = OUT_DIR / f"sft_val_{_sha1(str(n))}.jsonl"
    with open(train_p, "w", encoding="utf-8") as ft:
        for s in train:
            ft.write(json.dumps(s, ensure_ascii=False) + "\n")
    with open(val_p, "w", encoding="utf-8") as fv:
        for s in val:
            fv.write(json.dumps(s, ensure_ascii=False) + "\n")
    return {"train": str(train_p), "val": str(val_p)}


def build_sft_dataset(split_ratio: float = 0.98) -> Dict[str, str]:
    raise RuntimeError("disabled: vendor-output distillation is prohibited")
