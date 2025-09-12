[ "${TRAINING_ENABLED:-0}" = "1" ] || { echo "LLM builder OFF (vendor-only mode)"; exit 1; }
set -e
python arena/gating.py && echo "PASS" || (echo "FAIL"; exit 1)
