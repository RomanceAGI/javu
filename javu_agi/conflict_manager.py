class ConflictManager:
    def __init__(self):
        self.conflicts = []

    def detect_conflict(self, goal_a, goal_b):
        """
        Detect whether two goals overlap or conflict with each other.

        If the goals are identical no conflict is recorded.  A conflict is
        considered present when one goal string contains the other.  When a
        conflict is detected the pair is appended to ``self.conflicts`` and a
        warning is printed.

        Parameters
        ----------
        goal_a : Any
            The first goal to compare.
        goal_b : Any
            The second goal to compare.

        Returns
        -------
        bool
            True if there is a detected overlap, otherwise False.
        """
        if goal_a == goal_b:
            return False
        overlap = goal_a in goal_b or goal_b in goal_a
        if overlap:
            self.conflicts.append((goal_a, goal_b))
            print(f"⚠️ Conflict detected: {goal_a} ↔ {goal_b}")
        return overlap


    def resolve(self, goal_a, goal_b, priority_map):
        """
        Resolve a conflict between two goals by selecting the higher priority goal.

        Parameters
        ----------
        goal_a, goal_b : Any
            The goals that are in conflict.
        priority_map : dict
            A mapping from goals to a numeric priority score.

        Returns
        -------
        Any
            The goal with the higher priority score (ties broken in favour of ``goal_a``).
        """
        score_a = priority_map.get(goal_a, 0.5)
        score_b = priority_map.get(goal_b, 0.5)
        return goal_a if score_a >= score_b else goal_b
