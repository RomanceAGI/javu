import re
from types import SimpleNamespace


class FounderProtection:
    def __init__(self, founder_id: str = "roman", names=None):
        self.founder_id = founder_id
        self.names = set(n.lower() for n in (names or [founder_id]))
        self._threat = re.compile(r"\b(kill|harm|doxx|extort|harass)\b", re.I)

    def guard(self, user_id: str, text: str):
        t = text or ""
        if self._threat.search(t):
            return SimpleNamespace(
                allow=False, category="security:threat", reason="founder_protection"
            )
        return SimpleNamespace(allow=True, category="", reason="")
