[ "${TRAINING_ENABLED:-0}" = "1" ] || { echo "LLM builder OFF (vendor-only mode)"; exit 1; }
set -e
#!/usr/bin/env bash
set -euo pipefail
python eval_harness.py --schedule daily --metrics all --write_json arena_logs/daily/$(date +%F).json
