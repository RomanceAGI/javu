
#!/usr/bin/env bash
set -e
python3 -u tests_smoke/test_security.py
python3 -u tests_smoke/test_planner.py
python3 -u tests_smoke/test_multimodal.py || true
python3 -u tests_smoke/test_memory.py || true
