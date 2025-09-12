from __future__ import annotations
from typing import List, Dict, Any, Tuple, Optional
import math


class VectorStore:
    """Antarmuka generik; default: in-memory cosine."""

    def add(
        self,
        texts: List[str],
        metas: Optional[List[Dict[str, Any]]] = None,
        collection: str = "default",
    ): ...
    def search(
        self, query: str, k: int = 8, collection: str = "default"
    ) -> List[Tuple[str, float, Dict[str, Any]]]: ...


# ---- In-memory fallback (ringan, tanpa dep) ----
class InMemoryVectorStore(VectorStore):
    def __init__(self):
        self.db: Dict[str, List[Tuple[List[float], str, Dict[str, Any]]]] = {}

    def _embed(self, text: str) -> List[float]:
        # hashing bag-of-ngrams ringan
        dim = 256
        v = [0.0] * dim
        t = text.lower()
        for i in range(len(t) - 3):
            h = hash(t[i : i + 4]) % dim
            v[h] += 1.0
        n = math.sqrt(sum(x * x for x in v)) or 1.0
        return [x / n for x in v]

    def add(
        self,
        texts: List[str],
        metas: Optional[List[Dict[str, Any]]] = None,
        collection: str = "default",
    ):
        metas = metas or [{} for _ in texts]
        col = self.db.setdefault(collection, [])
        for txt, meta in zip(texts, metas):
            col.append((self._embed(txt[:4000]), txt[:4000], meta))

    def search(
        self, query: str, k: int = 8, collection: str = "default"
    ) -> List[Tuple[str, float, Dict[str, Any]]]:
        col = self.db.get(collection, [])
        if not col:
            return []
        qv = self._embed(query)

        def cos(a, b):
            return sum(x * y for x, y in zip(a, b))

        scored = [(txt, float(cos(qv, v)), meta) for (v, txt, meta) in col]
        scored.sort(key=lambda t: t[1], reverse=True)
        return scored[:k]
