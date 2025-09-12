[ "${TRAINING_ENABLED:-0}" = "1" ] || { echo "LLM builder OFF (vendor-only mode)"; exit 1; }
set -e
#!/usr/bin/env bash
set -euo pipefail
python - <<'PY'
import importlib, sys
for m in ["javu_agi.executive_controller","javu_agi.execution_manager"]:
    importlib.import_module(m)
print("IMPORT_OK")
PY
