import os, json, subprocess, shlex
from pathlib import Path
from typing import Dict

OUT = Path(os.getenv("AUTOTRAIN_OUT", "artifacts/autotrain"))


def _cmd(c: str):
    print(f"[eval] $ {c}")
    return subprocess.run(shlex.split(c), check=True)


def eval_model(local_ckpt_dir: str, report_name: str = "local_eval.json"):
    """
    Gunakan eval_harness.py lo: jalankan arena/transfer/adversarial terhadap local model.
    Asumsi llm_router bisa route provider 'local' -> model di local_ckpt_dir.
    """
    OUT.mkdir(parents=True, exist_ok=True)
    rep = OUT / report_name
    # contoh CLI; sesuaikan dengan eval_harness lo
    _cmd(f"python eval_harness.py --local-ckpt {local_ckpt_dir} --write {rep}")
    return str(rep)
