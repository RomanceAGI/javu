import os, json, time
from typing import Dict, Any


def _try_import(path):
    try:
        return __import__(path, fromlist=["*"])
    except Exception:
        return None


EvalH = _try_import("eval_harness")
QueueMod = _try_import("javu_agi.runtime.queue")
RunnerSh = os.getenv("RUNNER_SH", "scripts/run_arena.sh")


def _sh(cmd: str) -> int:
    import subprocess

    p = subprocess.Popen(cmd, shell=True)
    return p.wait()


def job_arena(payload: Dict[str, Any]):
    n = int(payload.get("n", 500))
    return _sh(f"{RunnerSh} --arena --n {n}")


def job_train(payload: Dict[str, Any]):
    steps = int(payload.get("steps", 100000))
    mods = ",".join(payload.get("modalities", ["text", "vision", "code", "voice"]))
    save_every = int(payload.get("save_every", 1000))
    resume = payload.get("resume", False)
    flag = "--resume" if resume else "--no-resume"
    return _sh(
        f'{RunnerSh} --train --steps {steps} --mixed_modalities "{mods}" --save_every {save_every} {flag}'
    )


def job_eval(payload: Dict[str, Any]):
    out = payload.get("write_json", "arena_logs/daily/latest.json")
    return _sh(f'{RunnerSh} --eval && cp arena_logs/daily/latest.json "{out}"')


def run_job(job: Dict[str, Any]):
    jtype = job["type"]
    payload = job.get("payload", {})
    if jtype == "arena":
        return job_arena(payload)
    if jtype == "train":
        return job_train(payload)
    if jtype == "eval":
        return job_eval(payload)
    raise ValueError(f"Unknown job type: {jtype}")


if __name__ == "__main__":
    # RQ worker entry via `rq worker javu` in container; this module provides the function.
    # Optional: direct loop for debug
    print("Worker module loaded.")
