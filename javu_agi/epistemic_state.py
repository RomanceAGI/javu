class EpistemicState:
    def __init__(self):
        self.known_facts = set()
        self.uncertain_facts = set()
        self.confidences = {}  # key: statement, value: 0.0 - 1.0

    def update_fact(self, statement: str, confidence: float):
        self.confidences[statement] = confidence
        if confidence >= 0.8:
            self.known_facts.add(statement)
        else:
            self.uncertain_facts.add(statement)

    def is_known(self, statement: str) -> bool:
        return statement in self.known_facts

    def get_confidence(self, statement: str) -> float:
        return self.confidences.get(statement, 0.0)

    def list_uncertain(self) -> list:
        return list(self.uncertain_facts)
