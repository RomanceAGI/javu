import re, os

PATTERNS = [
    r"\b\d{16}\b",  # card (kasar)
    r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
    r"\b\d{3}[- ]?\d{3}[- ]?\d{4}\b",  # phone simple
]
THR = float(os.getenv("PII_BLOCK_THRESHOLD", "0.0"))  # 0.0=block kalau ada


def leak_score(text: str) -> float:
    s = text or ""
    hits = 0
    for p in PATTERNS:
        hits += len(re.findall(p, s))
    return float(hits)


def is_leak(text: str) -> bool:
    return leak_score(text) > THR
