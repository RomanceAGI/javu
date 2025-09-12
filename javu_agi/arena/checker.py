from __future__ import annotations
import re, time
from typing import Dict, Tuple


def check(rule: Dict, text: str) -> bool:
    t = text or ""
    kind = (rule.get("check") or "contains").lower()
    val = str(rule.get("value", ""))
    if kind == "contains":
        return val.lower() in t.lower()
    if kind == "equals":
        return t.strip().lower() == val.strip().lower()
    if kind == "regex":
        try:
            return re.search(val, t, re.I) is not None
        except re.error:
            return False
    return False


def duel(execu, prompt: str, rule: Dict, modes=("S2", "S3")) -> Dict:
    """
    Jalankan 2 mode, nilai dengan `check(rule, text)`.
    Return: {"winner": "S2"/"S3"/"none", "s2": txt, "s3": txt}
    """
    t0 = time.time()
    out = {}
    s2_txt, _ = execu.process("arena", f"[{modes[0]}] {prompt}")
    s3_txt, _ = execu.process("arena", f"[{modes[1]}] {prompt}")
    ok2 = check(rule, s2_txt)
    ok3 = check(rule, s3_txt)
    if ok2 and not ok3:
        winner = modes[0]
    elif ok3 and not ok2:
        winner = modes[1]
    elif ok2 and ok3:
        # tie-break: lebih panjang (proxy ‘informatif’) → menang
        winner = modes[0] if len(s2_txt) >= len(s3_txt) else modes[1]
    else:
        winner = "none"
    out.update(
        {
            "winner": winner,
            "s2": s2_txt,
            "s3": s3_txt,
            "latency_ms": int((time.time() - t0) * 1000),
        }
    )
    return out
