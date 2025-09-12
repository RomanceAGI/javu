import re


def scrub(text: str) -> str:
    if not isinstance(text, str):
        return text
    t = re.sub(r"\b[\w\.-]+@[\w\.-]+\.\w+\b", "<email>", text)
    t = re.sub(r"\b(\+?\d[\d\-\s]{8,}\d)\b", "<phone>", t)
    t = re.sub(r"\b\d{16}\b", "<card>", t)
    return t
