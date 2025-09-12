from typing import List, Dict


class CollectiveGovernanceHub:
    """
    Deliberasi multi-stakeholder: agregasi preferensi, audit trade-off.
    """

    def __init__(self, stakeholders: List[str]):
        self.stakeholders = stakeholders

    def aggregate(self, proposals: List[Dict]) -> Dict:
        # Voting sederhana + fairness regularizer; bisa di-upgrade ke liquid democracy
        scored = [
            (p, p.get("public_good_score", 0.0) - 0.2 * p.get("inequality_risk", 0.0))
            for p in proposals
        ]
        best = max(scored, key=lambda x: x[1])[0] if scored else {}
        best["governance_note"] = "selected_by_collective_hub"
        return best

    def vote(self, proposals: List[Dict], context: Dict | None = None) -> Dict:
        return self.aggregate(proposals or [])
