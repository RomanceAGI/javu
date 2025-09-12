from typing import Dict, Any


class CausalEngine:
    """
    Stub kausal ringan: tempatkan causal prior & propagasi efek.
    Nanti bisa diupgrade ke do-calculus/pgmpy/dowhy.
    """

    def __init__(self, kg):
        self.kg = kg

    def propagate(
        self, action: str, outcome: Dict[str, Any], world: Dict[str, Any]
    ) -> Dict[str, Any]:
        # Heuristik sederhana sementara
        if outcome.get("effect") == "relocation":
            return {"energy_spent": 1}
        if outcome.get("effect") == "destructive":
            return {"damage": 1}
        return {}
