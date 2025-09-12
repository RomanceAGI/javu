from __future__ import annotations
from typing import List, Dict, Any, Tuple
import math

try:
    import faiss  # type: ignore
except Exception as e:
    faiss = None


class FaissVectorStore:
    """
    FAISS FlatIP dengan embedding hashing 4-gram (dim=256) supaya kompatibel
    dengan InMemory fallback. Simpel & cepat.
    """

    def __init__(self, dim: int = 256):
        if faiss is None:
            raise RuntimeError("FAISS not available")
        self.dim = dim
        self.index = faiss.IndexFlatIP(dim)
        self.vecs = []  # list[List[float]]
        self.texts: List[str] = []
        self.metas: List[Dict[str, Any]] = []

    def _embed(self, text: str) -> List[float]:
        dim = self.dim
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
        metas: List[Dict[str, Any]] | None = None,
        collection: str = "default",
    ):
        metas = metas or [{} for _ in texts]
        for txt, meta in zip(texts, metas):
            v = self._embed(txt[:4000])
            self.vecs.append(v)
            self.texts.append(txt[:4000])
            self.metas.append(meta)
        import numpy as np

        arr = np.array(self.vecs[-len(texts) :], dtype="float32")
        self.index.add(arr)

    def search(
        self, query: str, k: int = 8, collection: str = "default"
    ) -> List[Tuple[str, float, Dict[str, Any]]]:
        if len(self.texts) == 0:
            return []
        import numpy as np

        qv = self._embed(query)
        q = np.array([qv], dtype="float32")
        scores, ids = self.index.search(q, min(k, len(self.texts)))
        out = []
        for idx, sc in zip(ids[0], scores[0]):
            if int(idx) < 0:
                continue
            out.append((self.texts[int(idx)], float(sc), self.metas[int(idx)]))
        return out
