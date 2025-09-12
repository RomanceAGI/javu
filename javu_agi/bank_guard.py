from __future__ import annotations
import os, json, re

PII_PATTERNS = [
    r"\b\d{16}\b",  # kartu (sederhana)
    r"\b\d{3}-\d{2}-\d{4}\b",  # SSN-like
    r"\b\d{8,12}\b",  # NIK-like (heuristic)
    r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",  # email
]
SECRET_PATTERNS = [
    r"AKIA[0-9A-Z]{16}",  # AWS key
    r"ghp_[A-Za-z0-9]{30,}",  # GitHub token
    r"(?i)api[_-]?key\s*[:=]\s*[A-Za-z0-9_\-]{16,}",
]

DENY_TEXT = [
    "DDoS",
    "bypass rate limit",
    "keylogger",
    "ransomware",
    "exploit 0day",
    "dump database tanpa izin",
    "ambil data rahasia",
    "malware",
]


def is_safe_text(t: str) -> bool:
    s = t or ""
    if any(re.search(p, s) for p in PII_PATTERNS):
        return False
    if any(re.search(p, s) for p in SECRET_PATTERNS):
        return False
    ls = s.lower()
    if any(k in ls for k in (w.lower() for w in DENY_TEXT)):
        return False
    return True


def filter_bank(inp: str, out: str) -> int:
    kept = 0
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(inp, "r", encoding="utf-8") as fi, open(out, "w", encoding="utf-8") as fo:
        for line in fi:
            try:
                obj = json.loads(line)
                if is_safe_text(obj.get("prompt", "")):
                    fo.write(line)
                    kept += 1
            except Exception:
                continue
    return kept
