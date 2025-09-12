[ "${TRAINING_ENABLED:-0}" = "1" ] || { echo "LLM builder OFF (vendor-only mode)"; exit 1; }
set -e
#!/usr/bin/env bash
set -euo pipefail
HOURS=${1:-12}
echo "[soak] starting autopilot for $HOURS hours..."
docker compose exec -d javu python -m javu_agi.cli.autopilot
sleep "${HOURS}h" || true
echo "[soak] stopping..."
docker compose exec -T javu sh -lc 'echo true > /data/runtime/.stop'
sleep 10
docker compose exec -T javu sh -lc 'echo false > /data/runtime/.stop'
