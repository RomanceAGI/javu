import os, json, time
from pathlib import Path
from typing import Dict
from javu_agi.autotrain.dataset_builder import build_sft_dataset
from javu_agi.autotrain.trainer_hf import run_local, run_remote
from javu_agi.autotrain.evaluator import eval_model

AUTOTRAIN_OUT = Path(os.getenv("AUTOTRAIN_OUT", "artifacts/autotrain"))


def _cfg_from_env(base_ckpt_env: str, train_path: str, val_path: str, tag: str) -> Dict:
    out = AUTOTRAIN_OUT / f"runs/{tag}"
    out.mkdir(parents=True, exist_ok=True)
    return {
        "base_ckpt": os.getenv(base_ckpt_env, "meta-llama/Llama-3.1-8B"),
        "train_path": train_path,
        "val_path": val_path,
        "out_dir": str(out),
        "lr": float(os.getenv("SFT_LR", "2e-5")),
        "max_steps": int(os.getenv("SFT_MAX_STEPS", "3000")),
        "micro_bsz": int(os.getenv("SFT_MICRO_BATCH", "2")),
        "global_bsz": int(os.getenv("SFT_GLOBAL_BATCH", "64")),
        "save_every": int(os.getenv("SAVE_EVERY", "500")),
        "eval_every": int(os.getenv("EVAL_EVERY", "500")),
    }


class AutoTrainOrchestrator:
    """
    E2E: distill->dataset->train->eval->register router
    """

    def run(self, size: str = "7B", remote: bool = False) -> Dict:
        t0 = time.time()
        ds = build_sft_dataset()
        tag = f"SFT_{size}_{int(t0)}"
        cfg = _cfg_from_env(
            "BASE_CKPT_7B" if size == "7B" else "BASE_CKPT_13B",
            ds["train"],
            ds["val"],
            tag,
        )

        # TRAIN
        if remote:
            run_remote(cfg)
        else:
            run_local(cfg)

        # EVAL
        report = eval_model(cfg["out_dir"], report_name=f"eval_{tag}.json")

        # REGISTER ke router (model lokal)
        reg = {
            "id": f"local-{size}-{int(t0)}",
            "ckpt_dir": cfg["out_dir"],
            "registered_at": int(time.time()),
            "report": report,
        }
        reg_p = AUTOTRAIN_OUT / "registry.jsonl"
        with open(reg_p, "a", encoding="utf-8") as f:
            f.write(json.dumps(reg) + "\n")
        return reg

    def run(self, size: str = "7B", remote: bool = False) -> Dict:
        raise RuntimeError("disabled: builder/training is off in this phase")
