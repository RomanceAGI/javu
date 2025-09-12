from __future__ import annotations
from pathlib import Path
from typing import List, Dict
from javu_agi.rag.ingest import ingest_texts


def _read_texts(folder: str) -> List[str]:
    out = []
    for p in Path(folder).rglob("*"):
        if p.suffix.lower() in [".txt", ".md", ".log"]:
            try:
                # Reading user-provided text files can fail for many reasons (encoding
                # errors, permission issues, etc.). Catch broad exceptions here so
                # ingestion skips unreadable files without crashing. We explicitly
                # capture Exception instead of using a bare except to avoid hiding
                # system-exiting errors.
                out.append(p.read_text(encoding="utf-8")[:8000])
            except Exception:
                # Skip unreadable file and continue.
                continue
    return out


def auto_ingest(folder: str, collection: str = "agi_facts"):
    docs = _read_texts(folder)
    metas: List[Dict] = [{"path": str(i)} for i, _ in enumerate(docs)]
    if docs:
        ingest_texts(docs, metas, collection=collection)
    return len(docs)
