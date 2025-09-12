from javu_agi.memory.episodic_memory import EpisodicMemory
from javu_agi.memory.memory_semantic import SemanticMemory
from javu_agi.memory.memory_schemas import SemanticFact
from datetime import datetime
import uuid


class Consolidator:
    def __init__(self):
        self.episodic = EpisodicMemory()
        self.semantic = SemanticMemory()

    def run(self):
        recent_eps = self.episodic.recall_recent(limit=10)
        for ep in recent_eps:
            for thought in ep.thoughts:
                fact = SemanticFact(
                    fact_id=str(uuid.uuid4()),
                    content=thought,
                    source=ep.episode_id,
                    confidence=0.8,
                    timestamp=datetime.utcnow(),
                )
                self.semantic.store(fact)
