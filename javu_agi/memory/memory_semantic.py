from javu_agi.memory.memory_schemas import SemanticFact
from typing import List
from datetime import datetime
import json
from pathlib import Path

SEMANTIC_FILE = Path("data/memory/semantic.json")
SEMANTIC_FILE.parent.mkdir(parents=True, exist_ok=True)


class SemanticMemory:
    def __init__(self):
        if not SEMANTIC_FILE.exists():
            json.dump([], open(SEMANTIC_FILE, "w"))

    def store(self, fact: SemanticFact):
        data = json.load(open(SEMANTIC_FILE))
        data.append(fact.dict())
        json.dump(data, open(SEMANTIC_FILE, "w"), ensure_ascii=False, indent=2)

    def search(self, query: str, limit=5) -> List[SemanticFact]:
        data = json.load(open(SEMANTIC_FILE))
        # Simple BM25-like scoring
        scored = [(f, query.lower() in f["content"].lower()) for f in data]
        results = [SemanticFact(**f) for f, match in scored if match][:limit]
        return results
