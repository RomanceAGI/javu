import re, yaml, os

POL_PATH = os.getenv("GOV_POLICY_PATH", "javu_agi/governance/ethics_guard/policy.yaml")


class GovGuard:
    def __init__(self):
        self.cfg = yaml.safe_load(open(POL_PATH))

    def check(self, text: str):
        t = text.lower()
        for k, terms in self.cfg.get("deny", {}).items():
            for term in sum([v if isinstance(v, list) else [v] for v in terms], []):
                if term.lower() in t:
                    return False, k
        return True, ""

    def principles(self):
        return self.cfg.get("governance_principles", [])
