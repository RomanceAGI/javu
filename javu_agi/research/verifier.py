from __future__ import annotations
from typing import Dict, List
import math
from javu_agi.research.literature_index import query_literature


def _overlap(a: str, b: str) -> float:
    a = a.lower().split()
    b = b.lower().split()
    if not a or not b:
        return 0.0
    A = set(a)
    B = set(b)
    return len(A & B) / max(1, len(A | B))


def _cosine_bow(a: str, b: str) -> float:
    # proxy kecil—tanpa dep: token freq cosine
    from collections import Counter

    ca, cb = Counter(a.lower().split()), Counter(b.lower().split())
    keys = set(ca) | set(cb)
    if not keys:
        return 0.0
    dot = sum(ca[k] * cb[k] for k in keys)
    na = math.sqrt(sum(v * v for v in ca.values())) or 1.0
    nb = math.sqrt(sum(v * v for v in cb.values())) or 1.0
    return dot / (na * nb)


def verify_hypothesis(h: str, k: int = 8) -> Dict:
    """
    Verifikasi hipotesis vs literatur lokal:
    - ambil k dok paling relevan
    - skor = 0.6*cosine + 0.4*overlap (max over docs)
    Return: {score (0..1), evidence (List[str])}
    """
    docs = query_literature(h, k=k)
    if not docs:
        return {"score": 0.0, "evidence": []}
    best = 0.0
    for d in docs:
        s = 0.6 * _cosine_bow(h, d) + 0.4 * _overlap(h, d)
        best = max(best, s)
    # ambil 3 doc teratas utk konteks jawaban
    evidence = docs[:3]
    return {"score": float(min(1.0, best)), "evidence": evidence}
