from typing import List, Dict, Any

class SafetyChecker:
    """
    Safety gate sederhana berbasis nilai inti.
    True = lolos; False = blok.
    """

    def check(
        self, actions: List[Dict[str, Any]], context: Dict[str, Any] | None = None
    ) -> bool:
        try:
            from javu_agi.safety.safety_values import violates_core_values
        except Exception:
            # fallback sangat konservatif jika modul tidak ada
            return False
        text = " ".join(a.get("cmd", "") or str(a) for a in (actions or []))
        return not bool(violates_core_values(text))


class PolicyAdapter:
    """
    Adapt PolicyFilter/PolicyFilterHard -> interface .check(actions)->bool
    Menganggap actions ~ steps (list of dicts).
    """

    def __init__(self, policy_filter):
        self.pf = policy_filter

    def check(
        self, actions: List[Dict[str, Any]], context: Dict[str, Any] | None = None
    ) -> bool:
        try:
            res = self.pf.check(actions)
            return bool(res.get("ok", False))
        except Exception:
            return False


class EthicsCheckerAdapter:
    """
    Adapt EthicsEngine (punya .score/.rewrite_safe) -> interface .check(actions)->bool
    Kebijakan: allow jika tidak flagged dan skor >= 0.0 (tune sesuai kebutuhanmu).
    """

    def __init__(self, engine):
        self.engine = engine

    def check(
        self, actions: List[Dict[str, Any]], context: Dict[str, Any] | None = None
    ) -> bool:
        text = " ".join(a.get("cmd", "") or str(a) for a in (actions or []))
        try:
            res = self.engine.score(text, context or {})
            flagged = bool(res.get("flagged", False))
            score = float(res.get("score", 0.0))
            return (not flagged) and (score >= 0.0)
        except Exception:
            return False
