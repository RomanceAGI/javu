[ "${TRAINING_ENABLED:-0}" = "1" ] || { echo "LLM builder OFF (vendor-only mode)"; exit 1; }
set -e
#!/usr/bin/env bash
set -euo pipefail
SET=${1:-data/banks/transfer_test.jsonl}
echo "[transfer] set=$SET"
docker compose exec -T javu python -m javu_agi.core run transfer --set "$SET"
