from __future__ import annotations
from typing import List, Dict
from javu_agi.vector.router import get_store


def ingest_texts(texts: List[str], metas: List[Dict], collection: str = "agi_facts"):
    get_store().add(texts, metas, collection=collection)


def search(query: str, k: int = 8, collection: str = "agi_facts"):
    return get_store().search(query, k, collection)
