from dataclasses import dataclass, field
from typing import List, Dict, Any
import time


@dataclass
class CurriculumStage:
    name: str
    objectives: List[str]
    min_score: float = 0.75
    datasets: List[str] = field(default_factory=list)
    tools: List[str] = field(default_factory=list)


class DevelopmentalCurriculum:
    """
    Kurikulum bertahap ala 'child→adult' untuk AGI.
    Integrasi: dipanggil oleh LifelongLearningManager tiap episode.
    """

    def __init__(self, stages: List[CurriculumStage]):
        self.stages = stages
        self.idx = 0

    @property
    def current(self) -> CurriculumStage:
        return self.stages[self.idx]

    def should_advance(self, eval_scores: Dict[str, float]) -> bool:
        # Naik tahap jika semua objective key ≥ min_score
        if not eval_scores:
            return False
        ok = all(
            eval_scores.get(obj, 0.0) >= self.current.min_score
            for obj in self.current.objectives
        )
        return ok

    def advance(self):
        if self.idx < len(self.stages) - 1:
            self.idx += 1

    def export_state(self) -> Dict[str, Any]:
        return {"stage": self.current.name, "idx": self.idx, "ts": time.time()}
