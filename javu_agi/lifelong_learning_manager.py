from typing import Dict, Any
import os
from javu_agi.developmental_curriculum import DevelopmentalCurriculum, CurriculumStage
from javu_agi.skill_transfer import SkillTransfer


class LifelongLearningManager:
    """
    Orkestrator pembelajaran seumur hidup: rehearsal, consolidation,
    transfer antardomain, dan forgetting control.
    """

    def __init__(self, memory, evaluator, tool_registry):
        self.memory = memory
        self.evaluator = evaluator
        self.tool_registry = tool_registry
        self.transfer = SkillTransfer(memory)
        self.curriculum = DevelopmentalCurriculum(
            stages=[
                CurriculumStage(
                    "infancy", ["imitation", "safe_tool_use"], datasets=["toy_world"]
                ),
                CurriculumStage(
                    "childhood",
                    ["basic_reasoning", "prosocial_choice"],
                    datasets=["social_sims"],
                ),
                CurriculumStage(
                    "adolescence",
                    ["abstract_reasoning", "long_horizon"],
                    datasets=["math_mix", "strategy"],
                ),
                CurriculumStage(
                    "adulthood",
                    ["real_world_ops", "ethical_tradeoff"],
                    datasets=["real_ops"],
                ),
            ]
        )

    def step(self, agent) -> Dict[str, Any]:
        # 1) Evaluate stage objectives
        scores = self.evaluator.evaluate_objectives(self.curriculum.current.objectives)
        # 2) Transfer skills across tasks seen recently
        self.transfer.cross_domain_consolidate()
        # 3) Advance curriculum if ready
        if self.curriculum.should_advance(scores):
            self.curriculum.advance()
        # 4) Anti-forgetting via rehearsal
        self.transfer.scheduled_rehearsal()
        return {"stage": self.curriculum.current.name, "scores": scores}

    @staticmethod
    def gate_enabled() -> bool:
        return (
            os.getenv("ENABLE_LIFELONG", "0") == "1"
            and os.getenv("CANARY_APPROVED", "0") == "1"
        )

    def __new__(cls, *a, **k):
        if not cls.gate_enabled():
            raise RuntimeError("lifelong learning disabled (gate OFF)")
        return super().__new__(cls)
