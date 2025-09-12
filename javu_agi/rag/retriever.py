from __future__ import annotations
from typing import List, Callable
from javu_agi.rag.ingest import search


class HybridRetriever:
    """
    Retriever hibrida ringan:
    - half lexical (dari facts internal yang disuplai world model)
    - half vector (via vector store in-memory / adapter)
    Return: List[str] (teks konteks)
    """

    def __init__(self, facts_ref: Callable[[], list[str]]):
        self.facts_ref = facts_ref

    def retrieve(self, query: str, k: int = 8) -> List[str]:
        facts = self.facts_ref() or []
        # Lexical slice (kasar tapi murah)
        lex_hits = [
            f for f in facts if any(t in f.lower() for t in query.lower().split())
        ][: max(1, k // 2)]
        # Vector search (sisanya)
        vec_hits = search(query, k=max(1, k - len(lex_hits)))
        vec_texts = [t for (t, _score, _m) in vec_hits]
        # Gabung unik, preserve urutan
        out = list(dict.fromkeys(lex_hits + vec_texts))
        return out[:k]


class RagRetriever:
    """
    Minimal interface buat eval:
      - retrieve(query, k) -> list[{"text": str, "source": str, "score": float}]
    Implementasi dalam proyek lo boleh lebih kompleks; wrapper ini hanya nyamain interface.
    """

    def __init__(self, client=None):
        # kalau sudah ada vector_client di proyek lo, inject di sini
        self.client = client

    def retrieve(self, query: str, k: int = 5):
        # Panggil pipeline RAG lo yang ada sekarang.
        # Ganti isi fungsi ini biar manggil vector_client/ingest milik lo sendiri.
        try:
            docs = self.client.search(query, top_k=k) if self.client else []
        except Exception:
            docs = []
        # Normalisasi format
        out = []
        for d in docs[:k]:
            out.append(
                {
                    "text": d.get("text") or d.get("content") or "",
                    "source": d.get("source") or d.get("url") or "corpus",
                    "score": float(d.get("score", 0.0)),
                }
            )
        return out
