[ "${TRAINING_ENABLED:-0}" = "1" ] || { echo "LLM builder OFF (vendor-only mode)"; exit 1; }
set -e
#!/usr/bin/env bash
set -e
cd "$(dirname "$0")/.."
python3 scripts/gate_check.py || true
