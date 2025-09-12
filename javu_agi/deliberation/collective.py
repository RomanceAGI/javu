import random
from typing import List, Dict


class CollectiveDeliberator:
    def __init__(self):
        self.personas = [
            "ethics",
            "logic",
            "empathy",
            "eco",
            "prudence",
            "law",
            "culture",
        ]

    def consensus(self, plan: List[Dict]) -> Dict:
        votes = {}
        for p in self.personas:
            score = random.uniform(0.4, 0.9)
            votes[p] = score
        avg = sum(votes.values()) / len(votes)
        return {"consensus": avg, "votes": votes}
