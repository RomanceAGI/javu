class TheoryOfMind:
    def __init__(self):
        self.models = {}

    def update_model(self, agent_id, observable_behavior):
        if agent_id not in self.models:
            self.models[agent_id] = []
        self.models[agent_id].append(observable_behavior)

    def predict_intent(self, agent_id):
        if agent_id not in self.models:
            return "unknown"
        recent = self.models[agent_id][-1].lower()
        if "ask" in recent:
            return "seeking info"
        elif "goal" in recent:
            return "pursuing goal"
        elif "question" in recent:
            return "curiosity"
        return "idle"


class SocialCognition(TheoryOfMind):
    def score_reaction(self, text: str) -> float:
        t = (text or "").lower()
        bad = sum(1 for k in ["offend", "toxic", "harm"] if k in t)
        good = sum(1 for k in ["please", "thank", "care", "help"] if k in t)
        base = 0.6 + 0.05 * good - 0.1 * bad
        return max(0.0, min(1.0, base))
