[ "${TRAINING_ENABLED:-0}" = "1" ] || { echo "LLM builder OFF (vendor-only mode)"; exit 1; }
set -e
#!/usr/bin/env bash
set -euo pipefail
python -m pytest -q || true
python task_bank/migrator.py --lint --dedup
python eval_harness.py --subset smoke_test --metrics all
flake8 javu_agi || true
