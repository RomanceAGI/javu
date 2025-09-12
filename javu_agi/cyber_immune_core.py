import hashlib, json, time
from typing import Dict, Any


class CyberImmuneCore:
    """
    Sistem imun siber: deteksi anomali → isolasi → self-heal → forensik.
    Integrasi: pasang sebagai guard di api_server.py dan execution_sandbox.py
    """

    def __init__(self, watchdog, anomaly_detector, provenance_guard):
        self.watchdog = watchdog
        self.detector = anomaly_detector
        self.provenance = provenance_guard

    def scan_and_isolate(self, event: Dict[str, Any]) -> Dict[str, Any]:
        score = self.detector.score(event)
        action = "allow"
        if score > 0.95:
            self.watchdog.freeze_process(event.get("pid"))
            self.provenance.snapshot("pre_isolation", event)
            action = "isolate"
        return {
            "risk": score,
            "action": action,
            "ok": action == "allow",
            "isolated": action == "isolate",
            "ts": time.time(),
        }

    def self_heal(self):
        # Rollback model/weights/config jika hash mismatch
        if not self.provenance.verify_artifacts():
            self.provenance.rollback_to_last_trusted()
            return {"healed": True}
        return {"healed": False}
