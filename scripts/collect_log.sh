[ "${TRAINING_ENABLED:-0}" = "1" ] || { echo "LLM builder OFF (vendor-only mode)"; exit 1; }
set -e
#!/usr/bin/env bash
set -euo pipefail
OUT="logs/last24h_$(date +%F_%H%M).log"
docker compose logs --since 24h > "$OUT"
echo "[logs] written to $OUT"
