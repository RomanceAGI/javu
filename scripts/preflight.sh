#!/usr/bin/env bash
set -euo pipefail

echo "[preflight] creating data dirs..."
mkdir -p data/{banks,runtime,logs}
touch data/runtime/state.pkl
[[ -f data/runtime/.stop ]] || echo "false" > data/runtime/.stop
[[ -f data/runtime/goal_inbox.jsonl ]] || echo '{"t":0,"goal":"Boot"}' > data/runtime/goal_inbox.jsonl

echo "[preflight] checking env..."
: "${DATA_DIR:=/data}"; : "${RUNTIME_DIR:=/data/runtime}"
echo "DATA_DIR=$DATA_DIR  RUNTIME_DIR=$RUNTIME_DIR"

echo "[preflight] building image..."
docker compose build --no-cache

# Safety: blok kalau training/fine-tune nyala
if [[ "${TRAINING_ENABLED:-0}" == "1" ]]; then
  echo "ERROR: TRAINING_ENABLED=1 → builder mode forbidden"
  exit 1
fi

echo "[preflight] running smoke tests..."
timeout 10s python -m javu_agi.core run loop || true
python -m javu_agi.core run arena || true

echo "[preflight] API smoke..."
set +e
curl -fsS "http://localhost:${PORT:-8000}/healthz" && echo " healthz OK" || echo " healthz FAIL"
curl -fsS "http://localhost:${PORT:-8000}/statusz" && echo " statusz OK" || echo " statusz FAIL"
set -e

echo "[preflight] generating evidence..."
bash scripts/gen_evidence.sh

python - <<'PY'
from tool_summarizer import summarize
from tool_translator import translate
from tool_code_gen import generate_code
from tool_schema import generate_schema
from tool_appgen import generate_app_flow
from tool_unity_gen import generate_unity_script
print("SUM:", summarize("Tulisan panjang tentang ekologi dan AI")[:120])
print("TRN:", translate("We build a planetary-first REAL AGI")[:120])
print("COD:", generate_code("CLI to print system info")[:120])
print("SCH:", generate_schema("E-commerce app with cart, checkout, orders")[:120])
print("APP:", generate_app_flow("Banking mobile app with OTP & budgeting")[:120])
print("UNI:", generate_unity_script("2D player controller with jump & dash")[:120])
PY

echo "[preflight] done."