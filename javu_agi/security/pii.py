import re

_PATTERNS = [
    re.compile(r"(?i)\b(ktp|nik|npwp|passport)\b[^0-9]*([0-9]{8,})"),
    re.compile(r"\b[0-9]{16}\b"),  # kartu/identitas umum (kasar)
    re.compile(r"(?i)\b(ssn)\b[^0-9]*([0-9\-]{9,})"),
    re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9\-.]+"),  # email
    re.compile(r"\b(\+?\d{1,3}[-.\s]?)?(\d{3,4}[-.\s]?){2,4}\d\b"),  # telp kasar
    re.compile(r"\b(?:\d[ -]*?){13,19}\b"),  # kartu kredit (kasar)
]


def is_leak(s: str) -> bool:
    if not s or not isinstance(s, str):
        return False
    for rx in _PATTERNS:
        if rx.search(s):
            return True
    return False
