[ "${TRAINING_ENABLED:-0}" = "1" ] || { echo "LLM builder OFF (vendor-only mode)"; exit 1; }
set -e
#!/usr/bin/env bash
set -euo pipefail

# load env
set -a; source ./.env; set +a

# dirs
mkdir -p "$METRICS_DIR" "$ARTIFACTS_DIR" "$QUEUE_DIR" \
         "$RESULT_CACHE_DIR" "$SKILL_CACHE_DIR" \
         /artifacts/governance/reports

# base soak
python -m javu_agi.curriculum_runner --suite base --episodes 200 --sleep 0.5

# safety battery
python -m javu_agi.eval_harness --suite safety
