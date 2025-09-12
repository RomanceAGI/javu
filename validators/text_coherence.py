from __future__ import annotations
import re
from typing import Tuple, List, Dict, Any, Optional

def validate_text_minimal(txt: str) -> Tuple[bool, List[str], Optional[Dict[str, Any]]]:
    warns: List[str] = []
    if not txt or len(txt.strip()) < 40: warns.append("too_short")
    if txt.count("\n") < 1: warns.append("no_structure")
    if "```" in txt and "```" not in txt.strip().split("```")[-1]: warns.append("fence_unclosed")
    return (len(warns) == 0), warns, None

def score_text(txt: str, _parsed: Optional[Dict[str, Any]] = None) -> float:
    s = 0.4
    L = len(txt)
    if L >= 400: s += 0.2
    if txt.count("\n") >= 4: s += 0.2
    if re.search(r"(Conclusion|Ringkasan|Summary):", txt): s += 0.1
    return min(1.0, s)
