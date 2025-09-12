import re

PII = [
    r"\b\d{16}\b",  # kartu (kasar)
    r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",  # email
]
SECRETS = [
    r"AKIA[0-9A-Z]{16}",  # AWS key
    r"ghp_[A-Za-z0-9]{30,}",  # GitHub token
    r"(?i)(api[_-]?key|token)\s*[:=]\s*['\"]?[A-Za-z0-9_\-]{16,}",
]

MASK = "§§REDACTED§§"


def scrub(text: str) -> str:
    s = text or ""
    for p in PII + SECRETS:
        s = re.sub(p, MASK, s)
    return s
