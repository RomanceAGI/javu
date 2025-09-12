from __future__ import annotations
from pathlib import Path


def read_text_file(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""


def read_md_file(p: Path) -> str:
    return read_text_file(p)


def read_log_file(p: Path) -> str:
    text = read_text_file(p)
    return "\n".join(text.splitlines()[-3000:])  # limit tail


# tanpa dep PDF eksternal; nanti bisa tambah tika/poppler saat VPS
