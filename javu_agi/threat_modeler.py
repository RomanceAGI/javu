class ThreatModeler:
    """
    Generate skenario serangan/misuse untuk uji gate & guard.
    """

    def __init__(self):
        self.scenarios = []

    def generate(self, plan: list) -> list:
        threats = []
        for step in plan:
            if "data" in step:
                threats.append("Data exfiltration via " + step)
            if "execute" in step:
                threats.append("Malicious code injection risk in " + step)
        self.scenarios.extend(threats)
        return threats
