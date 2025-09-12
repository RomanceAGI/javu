import os
import sys
import time
import json
import argparse
import subprocess
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
DEFAULT_RUNNER = ROOT_DIR / "scripts" / "run_arena.sh"


def log(msg: str):
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}", flush=True)


def run_cmd(cmd: str):
    log(f"RUN: {cmd}")
    proc = subprocess.Popen(cmd, shell=True)
    proc.wait()
    if proc.returncode != 0:
        log(f"ERROR: exit code {proc.returncode}")
        sys.exit(proc.returncode)
    return proc.returncode


def mode_arena(n: int):
    run_cmd(f'"{DEFAULT_RUNNER}" --arena --n {n}')


def mode_train(steps: int, modalities: str, save_every: int, resume: bool):
    resume_flag = "--resume" if resume else "--no-resume"
    run_cmd(
        f'"{DEFAULT_RUNNER}" --train --steps {steps} '
        f'--mixed_modalities "{modalities}" --save_every {save_every} {resume_flag}'
    )


def mode_eval(write_json: str):
    Path(write_json).parent.mkdir(parents=True, exist_ok=True)
    run_cmd(f'"{DEFAULT_RUNNER}" --eval')
    # Copy hasil eval terakhir ke lokasi yang diminta
    latest = ROOT_DIR / "arena_logs" / "daily" / "latest.json"
    if latest.exists():
        with open(latest) as f:
            data = json.load(f)
        with open(write_json, "w") as out:
            json.dump(data, out, indent=2)
        log(f"Eval results copied to {write_json}")
    else:
        log("WARNING: No latest.json found after eval")


def main():
    ap = argparse.ArgumentParser(description="AGI Runner Orchestrator CLI (maximal)")
    ap.add_argument("--mode", required=True, choices=["arena", "train", "eval"])
    ap.add_argument("--n", type=int, default=500, help="Batch size untuk arena mode")
    ap.add_argument(
        "--steps", type=int, default=100000, help="Jumlah steps untuk training"
    )
    ap.add_argument(
        "--modalities",
        type=str,
        default="text,vision,code,voice",
        help="List modalities",
    )
    ap.add_argument(
        "--save_every", type=int, default=1000, help="Interval save checkpoint"
    )
    ap.add_argument(
        "--resume", action="store_true", help="Resume training dari checkpoint terakhir"
    )
    ap.add_argument(
        "--write_json",
        type=str,
        default="arena_logs/daily/latest_copy.json",
        help="Output JSON untuk mode eval",
    )
    args = ap.parse_args()

    start_time = time.time()
    log(f"Starting mode={args.mode}")

    if args.mode == "arena":
        mode_arena(args.n)
    elif args.mode == "train":
        mode_train(args.steps, args.modalities, args.save_every, args.resume)
    elif args.mode == "eval":
        mode_eval(args.write_json)

    elapsed = time.time() - start_time
    log(f"Completed in {elapsed:.2f}s")


if __name__ == "__main__":
    main()
