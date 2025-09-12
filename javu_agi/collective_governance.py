from collections import defaultdict


class CollectiveGovernance:
    """
    Voting multi-stakeholder untuk keputusan kritis.
    """

    def __init__(self):
        self.votes = defaultdict(list)

    def propose(self, proposal_id: str, text: str):
        self.votes[proposal_id] = []
        return {"proposal": proposal_id, "text": text}

    def cast_vote(self, proposal_id: str, voter: str, choice: str):
        self.votes[proposal_id].append((voter, choice))
        return {"proposal": proposal_id, "votes": self.votes[proposal_id]}

    def tally(self, proposal_id: str):
        counts = defaultdict(int)
        for _, choice in self.votes[proposal_id]:
            counts[choice] += 1
        verdict = max(counts, key=counts.get) if counts else "undecided"
        return {"proposal": proposal_id, "counts": dict(counts), "verdict": verdict}
