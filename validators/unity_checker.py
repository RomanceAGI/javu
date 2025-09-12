# validators/unity_checker.py
from __future__ import annotations
import os, re, subprocess, tempfile
from typing import Tuple, List

CLASS_RX = re.compile(r"\b(public\s+)?class\s+[A-Z]\w+", re.M)
NAMESPACE_RX = re.compile(r"\bnamespace\s+\w+", re.M)
USING_UNSAFE_RX = re.compile(r"\b(System\.IO|DllImport|System\.Net\.Sockets)\b")

def static_sanity(code: str) -> List[str]:
    errs = []
    if not NAMESPACE_RX.search(code): errs.append("missing namespace")
    if not CLASS_RX.search(code): errs.append("missing public class")
    if USING_UNSAFE_RX.search(code): errs.append("unsafe API usage detected")
    return errs

def roslyn_compile_check(code: str) -> List[str]:
    """Optional syntax check via Roslyn CSC if UNITY_CSC_PATH set."""
    csc = os.getenv("UNITY_CSC_PATH")
    if not csc or not os.path.exists(csc):
        return []  # skip if not available
    with tempfile.TemporaryDirectory() as td:
        fp = os.path.join(td, "Gen.cs")
        open(fp, "w", encoding="utf-8").write(code)
        try:
            out = subprocess.run([csc, fp], capture_output=True, text=True, timeout=10)
            if out.returncode != 0:
                return [l.strip() for l in (out.stderr or out.stdout).splitlines() if l.strip()]
        except Exception as e:
            return [f"csc_error: {e}"]
    return []

def quality_score(code: str) -> float:
    lines = [l for l in code.splitlines() if l.strip()]
    score = 0.5
    if NAMESPACE_RX.search(code): score += 0.1
    if CLASS_RX.search(code): score += 0.1
    if any(("Update(" in code, "Start(" in code)): score += 0.1
    if len(lines) >= 30: score += 0.1
    return max(0.0, min(1.0, score))
