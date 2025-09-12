import json
from pathlib import Path
from typing import List
from .schemas import Episode
from datetime import datetime

EPISODIC_DIR = Path("data/memory/episodic")
EPISODIC_DIR.mkdir(parents=True, exist_ok=True)


class EpisodicMemory:
    def __init__(self):
        self.path = EPISODIC_DIR

    def store(self, episode: Episode):
        file = self.path / f"{episode.episode_id}.json"
        with open(file, "w", encoding="utf-8") as f:
            json.dump(episode.dict(), f, ensure_ascii=False, indent=2)

    def recall_recent(self, limit=5) -> List[Episode]:
        files = sorted(
            self.path.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True
        )[:limit]
        return [Episode(**json.load(open(f))) for f in files]

    def recall_by_id(self, episode_id: str) -> Episode:
        file = self.path / f"{episode_id}.json"
        if file.exists():
            return Episode(**json.load(open(file)))
        return None
