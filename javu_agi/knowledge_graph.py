import json, os
from typing import Any, Dict
from collections import defaultdict


class KnowledgeGraph:
    """
    Graph ringan berbasis key->value + meta (bisa diganti ke Neo4j/graph DB nanti).
    """

    def __init__(self, path: str):
        self.path = path
        os.makedirs(os.path.dirname(path), exist_ok=True)
        self.data: Dict[str, Dict[str, Any]] = {}
        self._load()

    def _load(self):
        if os.path.exists(self.path):
            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    self.data = json.load(f)
            except Exception:
                # If the file cannot be read or parsed, start from an empty graph.
                self.data = {}

    def _save(self):
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)

    def upsert_fact(self, key: str, value: Any, source: str = "", ts: str = ""):
        self.data[key] = {"value": value, "src": source, "ts": ts}
        self._save()

    def query(self, key: str):
        item = self.data.get(key)
        return item["value"] if item else None

    def add(self, subj, rel, obj):
        self.E[subj].add((rel, obj))

    def neighbors(self, subj):
        return list(self.E.get(subj, []))

    def triples(self):
        for s, ro in self.E.items():
            for r, o in ro:
                yield (s, r, o)
