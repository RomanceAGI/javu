import logging, statistics

log = logging.getLogger("reflective")


class ReflectiveLoop:
    def __init__(self, window=20):
        self.journal = []
        self.window = window

    def log_decision(self, record: dict):
        self.journal.append(record)
        if len(self.journal) > self.window:
            self.journal.pop(0)

    def reflect(self) -> dict:
        """Analisis tren keputusan terakhir, cari potensi misalignment"""
        if not self.journal:
            return {"status": "empty"}
        harms = [1 for r in self.journal if r["verdict"] == "deny"]
        escalations = [1 for r in self.journal if r["verdict"] == "escalate"]
        avg_risk = statistics.mean([r["risk"].get("score", 0) for r in self.journal])
        report = {
            "total": len(self.journal),
            "deny_rate": len(harms) / len(self.journal),
            "escalate_rate": len(escalations) / len(self.journal),
            "avg_risk": avg_risk,
        }
        if report["deny_rate"] > 0.2 or report["avg_risk"] > 0.6:
            report["flag"] = "possible_drift"
            log.warning("ReflectiveLoop: drift detected %s", report)
        else:
            report["flag"] = "ok"
        return report
