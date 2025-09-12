class AnalogyEngine:
    def __init__(self):
        self.known_pairs = []

    def add_pair(self, domain_a, domain_b):
        self.known_pairs.append((domain_a, domain_b))

    def find_analogy(self, new_input):
        for a, b in self.known_pairs:
            if new_input.lower() in a.lower():
                return b
        return "Tidak ditemukan analogi"
