from __future__ import annotations
import os
from typing import List, Dict, Any, Tuple
from javu_agi.vector.store import InMemoryVectorStore

_BACKEND = None


def get_store():
    global _BACKEND
    if _BACKEND is not None:
        return _BACKEND
    backend = os.getenv("VECTOR_BACKEND", "memory").lower()
    if backend == "faiss":
        from javu_agi.vector.faiss_adapter import FaissVectorStore

        _BACKEND = FaissVectorStore(dim=256)
    elif backend == "pgvector":
        from javu_agi.vector.pgvector_adapter import PGVectorStore

        dsn = os.getenv("PG_DSN", "postgresql://user:pass@localhost:5432/db")
        _BACKEND = PGVectorStore(dsn=dsn, dim=256, use_cosine=True)
    else:
        _BACKEND = InMemoryVectorStore()
    return _BACKEND
