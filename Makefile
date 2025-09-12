.PHONY: test rct bench

test:
\tpytest -q

rct:
\tpython -m javu_agi.eval.rct_runner

bench:
\tpython -m javu_agi.eval.bench_runner datasets/sample.jsonl

arena:
\tpython -m javu_agi.arena.runner
curriculum:
\tpython - <<'PY'\nfrom javu_agi.learn.curriculum import build_default_curriculum as b; c=b(); print(c)\nPY

train:
\tpython -m javu_agi.train.loop

# ==== VENDOR-ONLY GUARD ====
TRAINING_ENABLED ?= 0

# Semua target yang berbau training/distill/autotrain -> NO-OP
train finetune autotrain distill builder retrain retraining:
	@echo "LLM builder OFF (vendor-only mode)"; exit 1

# Juga blok seluruh target yang diawali pattern ini (aman kalau ada variasi)
train-% finetune-% autotrain-% distill-% builder-%:
	@echo "LLM builder OFF (vendor-only mode)"; exit 1