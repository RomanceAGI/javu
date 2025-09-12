from __future__ import annotations
import os, hashlib
from typing import List, Dict


class KnowledgeIngestor:
    def __init__(self, vec_store: Dict[str, str] | None = None) -> None:
        self.store = vec_store or {}

    def add(self, doc_id: str, text: str) -> str:
        h = hashlib.sha1(text.encode()).hexdigest()[:12]
        self.store[doc_id + ":" + h] = text
        return h

    def search(self, query: str, k: int = 3) -> List[str]:
        # naive semantic search stub
        res = [txt for _, txt in list(self.store.items())[:k]]
        return res
