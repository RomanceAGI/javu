from __future__ import annotations
from typing import Dict


def synthesize_tool(desc: str) -> Dict[str, str]:
    # Template minimal; nanti bisa diganti via LLM router
    if "csv" in desc.lower():
        code = "import csv,sys\nr=csv.reader(sys.stdin)\nprint(sum(1 for _ in r))"
        return {"tool": "python", "cmd": f"python - <<'PY'\n{code}\nPY"}
    if "http" in desc.lower() or "url" in desc.lower():
        return {"tool": "bash", "cmd": "curl -sSL $URL | head -n 50"}
    return {"tool": "bash", "cmd": "echo 'todo: synth tool' "}
