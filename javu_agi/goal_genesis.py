import random

class GoalGenesis:
    def __init__(self):
        self.seed_goals = [
            "explore new tools",
            "reflect on past failure",
            "improve memory usage",
            "generate new hypothesis",
            "learn user preference",
        ]

    def generate(self, memory_snapshot):
        """
        Generate a new goal based on a memory snapshot.

        If there are any unresolved questions (denoted by a '?' or the phrase
        'belum jelas') in the memory, an exploratory goal is returned using the
        most recent such item.  Otherwise a seed goal is selected at random.

        Parameters
        ----------
        memory_snapshot : iterable
            A collection of recent memory strings.

        Returns
        -------
        str
            A suggested new goal.
        """
        relevant = [m for m in memory_snapshot if "?" in m or "belum jelas" in m]
        if relevant:
            return "eksplorasi: " + relevant[-1]
        return random.choice(self.seed_goals)
