[ "${TRAINING_ENABLED:-0}" = "1" ] || { echo "LLM builder OFF (vendor-only mode)"; exit 1; }
set -e
#!/usr/bin/env bash
set -euo pipefail
python -m compileall -q .
pyflakes javu_agi | sed 's/^/pyflakes: /' || true
pytest -q tests/test_immune_block.py -q
pytest -q tests/test_contracts_enforce.py -q
pytest -q tests/test_peace_opt.py -q
echo "OK"
