[ "${TRAINING_ENABLED:-0}" = "1" ] || { echo "LLM builder OFF (vendor-only mode)"; exit 1; }
set -e
#!/usr/bin/env bash
# JAVU AGI runner (arena/train/eval) — v1.2
# - Autodetect docker compose service or run local
# - Support: --arena/--train/--eval
# - Extras: --steps, --n, --mixed_modalities, --service, --no-docker, --resume/--no-resume

set -euo pipefail

MODE="arena"        # arena|train|eval
N=500
STEPS=100000
MIXED_MODALITIES="text,vision,code,voice"
SERVICE="${SERVICE:-javu}"
USE_DOCKER=1
RESUME=1
SAVE_EVERY=1000

# ---------- args ----------
while [[ $# -gt 0 ]]; do
  case "$1" in
    --arena) MODE="arena"; shift;;
    --train) MODE="train"; shift;;
    --eval)  MODE="eval";  shift;;
    --n) N="$2"; shift 2;;
    --steps) STEPS="$2"; shift 2;;
    --mixed_modalities) MIXED_MODALITIES="$2"; shift 2;;
    --service) SERVICE="$2"; shift 2;;
    --no-docker) USE_DOCKER=0; shift;;
    --resume) RESUME=1; shift;;
    --no-resume) RESUME=0; shift;;
    --save_every) SAVE_EVERY="$2"; shift 2;;
    *) echo "unknown arg: $1"; exit 1;;
  esac
done

# ---------- helpers ----------
run_py () {
  local mod="$1"; shift
  if [[ "$USE_DOCKER" == "1" ]]; then
    docker compose exec -T "$SERVICE" python -m "$mod" "$@"
  else
    python -m "$mod" "$@"
  fi
}

run_file () {
  local file="$1"; shift
  if [[ "$USE_DOCKER" == "1" ]]; then
    docker compose exec -T "$SERVICE" python "$file" "$@"
  else
    python "$file" "$@"
  fi
}

mkdir -p arena_logs/daily logs

# ---------- modes ----------
if [[ "$MODE" == "arena" ]]; then
  echo "[arena] running $N tasks..."
  # prefer core launcher if exists, else fallback to API in root main.py
  if [[ "$USE_DOCKER" == "1" ]]; then
    if docker compose exec -T "$SERVICE" python -c "import javu_agi.core" >/dev/null 2>&1; then
      run_py javu_agi.core run arena --n "$N" | tee >(sed -n '1,120p' >&2) > logs/arena_stdout.txt || true
    else
      run_file main.py --mode arena --n "$N" | tee >(sed -n '1,120p' >&2) > logs/arena_stdout.txt || true
    fi
  else
    if python - <<'PY' 2>/dev/null; then
import importlib, sys
sys.exit(0 if importlib.util.find_spec("javu_agi.core") else 1)
PY
    then
      run_py javu_agi.core run arena --n "$N" | tee >(sed -n '1,120p' >&2) > logs/arena_stdout.txt || true
    else
      run_file main.py --mode arena --n "$N" | tee >(sed -n '1,120p' >&2) > logs/arena_stdout.txt || true
    fi
  fi
fi

if [[ "$MODE" == "train" ]]; then
  echo "[train] steps=$STEPS modalities=$MIXED_MODALITIES resume=$RESUME save_every=$SAVE_EVERY"
  RESUME_FLAG=""
  [[ "$RESUME" == "1" ]] && RESUME_FLAG="--resume"
  if [[ "$USE_DOCKER" == "1" ]]; then
    if docker compose exec -T "$SERVICE" python -c "import javu_agi.train.main" >/dev/null 2>&1; then
      run_py javu_agi.train.main --steps "$STEPS" --modalities $(echo "$MIXED_MODALITIES" | tr ',' ' ') --save_every "$SAVE_EVERY" $RESUME_FLAG
    else
      run_file main.py --mode train --steps "$STEPS" --modalities "$MIXED_MODALITIES" --save_every "$SAVE_EVERY" $RESUME_FLAG
    fi
  else
    if python -c "import javu_agi.train.main" >/dev/null 2>&1; then
      run_py javu_agi.train.main --steps "$STEPS" --modalities $(echo "$MIXED_MODALITIES" | tr ',' ' ') --save_every "$SAVE_EVERY" $RESUME_FLAG
    else
      run_file main.py --mode train --steps "$STEPS" --modalities "$MIXED_MODALITIES" --save_every "$SAVE_EVERY" $RESUME_FLAG
    fi
  fi
fi

if [[ "$MODE" == "eval" ]]; then
  echo "[eval] writing daily metrics to arena_logs/daily/latest.json"
  if [[ "$USE_DOCKER" == "1" ]]; then
    if docker compose exec -T "$SERVICE" python -c "import eval_harness" >/dev/null 2>&1; then
      docker compose exec -T "$SERVICE" python eval_harness.py --schedule daily --write_json /app/arena_logs/daily/latest.json
    else
      run_file main.py --mode eval --write_json "arena_logs/daily/latest.json"
    fi
  else
    if python -c "import eval_harness" >/dev/null 2>&1; then
      python eval_harness.py --schedule daily --write_json arena_logs/daily/latest.json
    else
      run_file main.py --mode eval --write_json "arena_logs/daily/latest.json"
    fi
  fi
fi

echo "[runner] done."
