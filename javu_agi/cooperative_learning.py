class CooperativeLearning:
    """
    Pastikan AGI belajar berkolaborasi dengan agent lain,
    bukan kompetisi destruktif.
    """

    def __init__(self):
        self.history = []

    def interact(self, agent_id: str, outcome: str):
        self.history.append((agent_id, outcome))
        coop_score = sum(1 for _, o in self.history if o == "cooperate") / len(
            self.history
        )
        return {"coop_score": coop_score}
