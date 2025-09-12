class AlignmentAuditor:
    """
    Auditor independen: cek apakah keputusan EC konsisten dengan ValueMemory & NormativeFramework.
    """

    def __init__(self, value_memory, normative_framework):
        self.value_memory = value_memory
        self.normative_framework = normative_framework
        self.reports = []

    def audit(self, decision: dict) -> dict:
        issues = []
        for v in self.value_memory.get_all_values():
            if v not in decision.get("rationale", ""):
                issues.append(f"Value {v} not referenced")
        if decision.get("risk", 0) > 0.7:
            issues.append("High risk detected")
        report = {"decision": decision, "issues": issues}
        self.reports.append(report)
        return report
