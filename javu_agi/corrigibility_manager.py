from typing import Dict


class CorrigibilityManager:
    """
    Menjamin agen mau dikoreksi/dihentikan & mematuhi override manusia.
    """

    def __init__(self, consent_guard, ethics_gate):
        self.consent_guard = consent_guard
        self.ethics_gate = ethics_gate

    def override(self, command: Dict) -> Dict:
        # Validasi hak manusia & keselamatan
        if not self.consent_guard.authorize(command.get("user_id")):
            return {"accepted": False, "reason": "unauthorized"}
        if not self.ethics_gate.allow_override(command):
            return {"accepted": False, "reason": "unsafe_override"}
        # Terapkan
        return {"accepted": True, "action": command.get("action")}
