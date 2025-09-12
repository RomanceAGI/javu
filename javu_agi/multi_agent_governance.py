from typing import Dict, List


class ReputationLedger:
    def __init__(self):
        self.rep = {}  # agent_id -> score

    def update(self, agent_id: str, delta: float):
        self.rep[agent_id] = self.rep.get(agent_id, 0.0) + delta

    def score(self, agent_id: str) -> float:
        return self.rep.get(agent_id, 0.0)


class MultiAgentGovernance:
    """
    Protokol kooperasi: kontrak tugas, reputasi, dan sanksi lembut.
    """

    def __init__(self):
        self.ledger = ReputationLedger()

    def propose_contract(self, task: Dict, agents: List[str]) -> Dict:
        # Bagi tugas berdasarkan keahlian & reputasi
        allocation = {a: task.get("subtasks", [])[:1] for a in agents}
        return {"allocation": allocation, "policy": "graceful_defection"}

    def settle_outcome(self, outcomes: Dict[str, bool]):
        for a, ok in outcomes.items():
            self.ledger.update(a, 1.0 if ok else -1.0)
