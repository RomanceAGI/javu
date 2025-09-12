import json, os
from typing import Dict, List, Any


class EpisodicMemory:
    def __init__(self, path: str):
        self.path = path
        os.makedirs(os.path.dirname(path), exist_ok=True)

    def store(self, event: Dict[str, Any]):
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")

    def load_last(self, n: int = 50) -> List[Dict[str, Any]]:
        if not os.path.exists(self.path):
            return []
        with open(self.path, "r", encoding="utf-8") as f:
            lines = f.readlines()[-n:]
        return [json.loads(x) for x in lines]
