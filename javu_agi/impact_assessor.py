from typing import Dict


class ImpactAssessor:
    """
    Skor dampak multi-dimensi: manusia, komunitas, ekologi, ekonomi.
    Output dipakai di planner untuk penalize/boost rencana.
    """

    def score(self, plan: Dict) -> Dict[str, float]:
        # TODO: hubungkan ke sustainability_model.py + social_cost datasets
        human = self._human_benefit(plan)
        community = self._community_cohesion(plan)
        ecology = self._ecology_footprint(plan)
        economic = self._inclusive_economy(plan)
        composite = 0.35 * human + 0.25 * community + 0.25 * ecology + 0.15 * economic
        return {
            "human": human,
            "community": community,
            "ecology": ecology,
            "economic": economic,
            "composite": composite,
        }

    def assess(self, steps_or_plan: Dict) -> Dict[str, float]:
        plan = (
            steps_or_plan
            if isinstance(steps_or_plan, dict)
            else {"steps": steps_or_plan or []}
        )
        return self.score(plan)

    def _human_benefit(self, plan):
        return 1.0 - plan.get("harm_prob", 0.0)

    def _community_cohesion(self, plan):
        return 1.0 - plan.get("polarization_risk", 0.0)

    def _ecology_footprint(self, plan):
        return max(
            0.0,
            1.0
            - plan.get("energy_cost", 0.0) * 0.1
            - plan.get("resource_cost", 0.0) * 0.1,
        )

    def _inclusive_economy(self, plan):
        return 1.0 - plan.get("inequality_risk", 0.0)
