class LogicReasoner:
    def __init__(self):
        self.facts = set()

    def add_fact(self, fact):
        self.facts.add(fact)

    def query(self, query_str):
        return query_str in self.facts

    def infer(self, premise, conclusion):
        if premise in self.facts:
            self.facts.add(conclusion)
            return True
        return False

    def explain(self, statement):
        if statement in self.facts:
            return f"{statement} diketahui dari fakta."
        return f"{statement} belum bisa disimpulkan."
