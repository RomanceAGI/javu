class MentalSimulator:
    def __init__(self):
        self.scenarios = []

    def simulate(self, context, action):
        outcome = f"Dalam konteks '{context}', jika melakukan '{action}', maka kemungkinan hasil: berhasil sebagian."
        self.scenarios.append((context, action, outcome))
        return outcome

    def recall_simulations(self):
        return self.scenarios[-5:]
