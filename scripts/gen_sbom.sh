[ "${TRAINING_ENABLED:-0}" = "1" ] || { echo "LLM builder OFF (vendor-only mode)"; exit 1; }
set -e
#!/usr/bin/env bash
set -euo pipefail
mkdir -p artifacts
pip-compile --no-emit-index-url --no-annotate -o requirements.lock.txt requirements.txt
python - <<'PY'
import pathlib,hashlib,json,os
out={"files":[]}
for p in pathlib.Path("javu_agi").rglob("*.py"):
    h=hashlib.sha256(p.read_bytes()).hexdigest()
    out["files"].append({"path": str(p), "sha256": h})
pathlib.Path("artifacts/sbom.files.json").write_text(json.dumps(out,indent=2))
PY
