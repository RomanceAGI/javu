class IdentityAgent:
    def __init__(self, name="JAVU", traits=None):
        self.name = name
        self.traits = traits or {"curiosity": 1.0}
        self.experience = []

    def decide(self, percept, goal):
        self.experience.append({"percept": percept, "goal": goal})
        return f"Lakukan aksi untuk mencapai goal: {goal}"

    def __repr__(self):
        return f"<IdentityAgent name={self.name} traits={self.traits}>"
