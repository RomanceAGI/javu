[ "${TRAINING_ENABLED:-0}" = "1" ] || { echo "LLM builder OFF (vendor-only mode)"; exit 1; }
set -e
#!/usr/bin/env bash
set -euo pipefail
LIMIT=${LLM_DAILY_USD_LIMIT:-20}
USED_FILE="logs/cost_today.txt"
USED=$(awk '{s+=$1} END {print s+0}' "$USED_FILE" 2>/dev/null || echo 0)
echo "[cost] used=$USED limit=$LIMIT"
if awk -v u="$USED" -v l="$LIMIT" 'BEGIN{exit !(u>l)}'; then
  echo "[cost] LIMIT EXCEEDED → pausing via .stop"
  docker compose exec -T javu sh -lc 'echo true > /data/runtime/.stop'
fi
