class NarrativeModel:
    def __init__(self):
        self.events = []

    def observe(self, sentence):
        self.events.append(sentence)

    def summarize(self):
        if not self.events:
            return "Belum ada narasi."
        return f"Narasi saat ini: {self.events[-1]}"
