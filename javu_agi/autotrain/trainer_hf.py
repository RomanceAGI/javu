import os, json, subprocess, shlex
from pathlib import Path
from typing import Dict

OUT = Path(os.getenv("AUTOTRAIN_OUT", "artifacts/autotrain"))
OUT.mkdir(parents=True, exist_ok=True)


def _cmd(c: str):
    print(f"[train] $ {c}")
    return subprocess.run(shlex.split(c), check=True)


def write_train_script(cfg: Dict) -> str:
    """
    Generate script train_sft.py (transformers Trainer) di OUT, return path file.
    cfg: {base_ckpt, train_path, val_path, out_dir, lr, max_steps, micro_bsz, global_bsz, save_every, eval_every}
    """
    out_dir = Path(cfg["out_dir"])
    out_dir.mkdir(parents=True, exist_ok=True)
    py = out_dir / "train_sft.py"
    py.write_text(
        f"""
import os, json
from datasets import load_dataset
from transformers import AutoModelForCausalLM, AutoTokenizer, TrainingArguments, Trainer, DataCollatorForLanguageModeling

BASE="{cfg['base_ckpt']}"
TRAIN="{cfg['train_path']}"
VAL="{cfg['val_path']}"
OUTDIR="{cfg['out_dir']}"
LR={cfg['lr']}
MAX_STEPS={cfg['max_steps']}
MICRO_BSZ={cfg['micro_bsz']}
GLOBAL_BSZ={cfg['global_bsz']}
EVAL_EVERY={cfg['eval_every']}
SAVE_EVERY={cfg['save_every']}

tok = AutoTokenizer.from_pretrained(BASE, use_fast=True)
tok.padding_side = "left"
tok.truncation_side = "left"

def _tok(batch):
    return tok(batch["prompt"] + "\\n\\n### Response:\\n" + batch["response"], truncation=True)

train = load_dataset("json", data_files=TRAIN, split="train")
val   = load_dataset("json", data_files=VAL,   split="train")
train = train.map(_tok, batched=True, remove_columns=train.column_names)
val   = val.map(_tok, batched=True, remove_columns=val.column_names)

model = AutoModelForCausalLM.from_pretrained(BASE)

args = TrainingArguments(
    output_dir=OUTDIR,
    learning_rate=LR,
    per_device_train_batch_size=MICRO_BSZ,
    per_device_eval_batch_size=MICRO_BSZ,
    gradient_accumulation_steps=max(1, GLOBAL_BSZ//MICRO_BSZ),
    max_steps=MAX_STEPS,
    save_steps=SAVE_EVERY,
    evaluation_strategy="steps",
    eval_steps=EVAL_EVERY,
    logging_steps=50,
    bf16=True if torch.cuda.is_available() else False,
    report_to="none"
)

data_collator = DataCollatorForLanguageModeling(tok, mlm=False)
def _metrics(eval_pred): return {{}}

trainer = Trainer(
    model=model, tokenizer=tok,
    args=args, train_dataset=train, eval_dataset=val,
    data_collator=data_collator, compute_metrics=_metrics
)
trainer.train()
model.save_pretrained(OUTDIR)
tok.save_pretrained(OUTDIR)
print("OK")
""".strip(),
        encoding="utf-8",
    )
    return str(py)


def run_local(cfg: Dict):
    script = write_train_script(cfg)
    _cmd(f"python {script}")


def run_remote(cfg: Dict):
    host = os.getenv("REMOTE_GPU_HOST", "")
    user = os.getenv("REMOTE_GPU_USER", "")
    key = os.getenv("REMOTE_GPU_KEY_PATH", "")
    rdir = os.getenv("REMOTE_TRAIN_DIR", "/srv/autotrain")
    if not (host and user and key):
        raise RuntimeError("REMOTE_GPU_* not set")
    Path(OUT / "pack").mkdir(parents=True, exist_ok=True)
    cfg_p = OUT / "pack" / "cfg.json"
    cfg_p.write_text(json.dumps(cfg), encoding="utf-8")
    # sync
    _cmd(f"ssh -i {key} {user}@{host} 'mkdir -p {rdir}'")
    _cmd(f"scp -i {key} -r {OUT}/pack {user}@{host}:{rdir}/")
    # remote run (assume python env tersedia)
    _cmd(
        f"ssh -i {key} {user}@{host} 'cd {rdir}/pack && python - <<PY\n"
        f'import json, trainer_hf; cfg=json.load(open("cfg.json")); trainer_hf.run_local(cfg)\nPY\''
    )


def write_train_script(cfg: Dict) -> str:
    raise RuntimeError("disabled")


def run_local(cfg: Dict):
    raise RuntimeError("disabled")


def run_remote(cfg: Dict):
    raise RuntimeError("disabled")
