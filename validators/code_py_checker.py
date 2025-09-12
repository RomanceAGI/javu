from __future__ import annotations
import py_compile, tempfile, os
from typing import Tuple, List, Optional, Dict

def validate_python(code: str) -> Tuple[bool, List[str], Optional[Dict[str, Any]]]:
    if "import os" in code and "remove(" in code:  # ultra fast safety smell
        return False, ["dangerous_os_remove"], None
    try:
        with tempfile.TemporaryDirectory() as td:
            fp = os.path.join(td, "gen.py")
            open(fp, "w", encoding="utf-8").write(code)
            py_compile.compile(fp, doraise=True)
        return True, [], None
    except Exception as e:
        return False, [f"py_compile_error:{e}"], None

def score_python(code: str, _parsed=None) -> float:
    s = 0.5
    if "def " in code: s += 0.1
    if "if __name__" in code: s += 0.1
    if len(code.splitlines()) >= 30: s += 0.1
    return min(1.0, s)
