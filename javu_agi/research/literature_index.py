from __future__ import annotations
from pathlib import Path
from typing import List, Dict
from javu_agi.rag.ingest import ingest_texts, search

LIT_COLLECTION = "literature_local"

SUPPORT = {
    ".txt": True,
    ".md": True,
}


def _read(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""


def index_folder(folder: str, limit_chars: int = 8000) -> int:
    """Index korpus sains lokal (txt/md) → vector store collection 'literature_local'."""
    root = Path(folder)
    if not root.exists():
        return 0
    docs: List[str] = []
    metas: List[Dict] = []
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        if p.suffix.lower() not in SUPPORT:
            continue
        t = _read(p)[:limit_chars]
        if not t.strip():
            continue
        docs.append(t)
        metas.append({"path": str(p.resolve())})
    if docs:
        ingest_texts(docs, metas, collection=LIT_COLLECTION)
    return len(docs)


def query_literature(q: str, k: int = 8) -> List[str]:
    hits = search(q, k=k, collection=LIT_COLLECTION)
    return [t for (t, _s, _m) in hits]
