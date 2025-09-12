import os
import subprocess
import sys
from pathlib import Path

def test_env_defaults():
    assert os.environ.get("VENDOR_ONLY_MODE", "1") == "1"
    assert os.environ.get("ENABLE_SELF_LEARN", "0") == "0"

def test_py_compile_all():
    root = Path(__file__).resolve().parents[1]
    proc = subprocess.run([sys.executable, "scripts/run_pycompile.py"], cwd=root)
    assert proc.returncode == 0

def test_imports_critical():
    # Import critical modules if they exist; ignore if not present.
    for mod in ["api_server", "executive_controller", "llm_router", "main_agi_loop"]:
        try:
            __import__(mod)
        except ModuleNotFoundError:
            pass
