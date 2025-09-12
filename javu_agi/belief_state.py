class BeliefState:
    def __init__(self):
        self.beliefs = {}  # key: proposition, value: confidence

    def update(self, belief: str, confidence: float):
        self.beliefs[belief] = confidence

    def contradicts(self, other_belief: str) -> bool:
        """
        Determine if the given belief contradicts any existing high‑confidence beliefs.

        A contradiction is considered present when ``other_belief`` appears as a substring
        of a stored belief that has a confidence greater than 0.7.

        Parameters
        ----------
        other_belief : str
            The belief to test for contradiction against the current state.

        Returns
        -------
        bool
            True if a contradiction is detected, otherwise False.
        """
        for b, conf in self.beliefs.items():
            if b != other_belief and other_belief in b and conf > 0.7:
                return True
        return False


    def most_uncertain(self) -> str:
        if not self.beliefs:
            return None
        return min(self.beliefs.items(), key=lambda x: x[1])[0]
