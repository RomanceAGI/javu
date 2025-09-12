import logging
import json
import time
import uuid
from pathlib import Path
from dataclasses import dataclass, asdict, field
from typing import Any, Dict, List, Optional

# Data Classes

@dataclass
class Event:
    kind: str
    message: str
    timestamp: float = field(default_factory=lambda: time.time())
    run_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    tags: List[str] = field(default_factory=list)
    data: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class SafetyIncident(Event):
    severity: str = "medium"
    mitigation: str = ""
    rationale: str = ""

    def __post_init__(self):
        self.kind = "safety_incident"


@dataclass
class LoopReport(Event):
    loop_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    decision: str = ""
    rationale: str = ""
    outcome: str = ""

    def __post_init__(self):
        self.kind = "loop_report"

# Governance Orchestrator

class Governance:
    """Load governance docs and enforce them at runtime."""

    def __init__(self, base_dir: str = "javu_agi_final"):
        self.base = Path(base_dir)
        self.threat_model = self._load("THREAT_MODEL.md")
        self.safety_eval = self._load("SAFETY_EVAL_REPORT.md")
        self.model_card = self.base / "MODEL_CARD.md"
        self.final_report = self.base / "FINALIZATION_REPORT.md"
        self.runbook = self._load("RUNBOOK.md")

    def _load(self, filename: str) -> str:
        path = self.base / filename
        if path.exists():
            return path.read_text(encoding="utf-8", errors="ignore")
        return ""

    def list_threats(self) -> List[str]:
        """Extract threats from THREAT_MODEL.md (naive parse)."""
        return [line.strip("- ").strip() for line in self.threat_model.splitlines() if line.startswith("- ")]

    def list_safety_checks(self) -> List[str]:
        """Extract safety items from SAFETY_EVAL_REPORT.md (naive parse)."""
        return [line.strip("- ").strip() for line in self.safety_eval.splitlines() if line.startswith("- ")]

    def runbook_steps(self) -> List[str]:
        return [line.strip("- ").strip() for line in self.runbook.splitlines() if line.startswith("- ")]

    def export_to_model_card(self, content: str):
        with open(self.model_card, "a", encoding="utf-8") as f:
            f.write(f"\n### Governance Update\n{content}\n")

    def export_to_final_report(self, content: str):
        with open(self.final_report, "a", encoding="utf-8") as f:
            f.write(f"\n### Runtime Report\n{content}\n")

# Reporter

class Reporter:
    """Structured reporter with governance enforcement."""

    def __init__(self, governance: Governance, logfile: Optional[str] = None):
        self.gov = governance
        self.logfile = logfile
        self.logger = logging.getLogger("governance.reporter")
        self.logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("%(message)s"))
        self.logger.addHandler(handler)

    def _write(self, event: Event):
        payload = json.dumps(event.to_dict(), ensure_ascii=False)
        self.logger.info(payload)
        if self.logfile:
            with open(self.logfile, "a", encoding="utf-8") as f:
                f.write(payload + "\n")

    def report_event(self, kind: str, message: str, **kwargs):
        e = Event(kind=kind, message=message, data=kwargs)
        self._write(e)
        return e.run_id

    def report_safety(self, message: str, severity="medium", mitigation="", rationale="", **kwargs):
        e = SafetyIncident(message=message, severity=severity,
                           mitigation=mitigation, rationale=rationale,
                           data=kwargs, kind="safety_incident")
        self._write(e)
        self.gov.export_to_final_report(f"[SAFETY] {message} | Mitigation: {mitigation}")
        return e.run_id

    def report_loop(self, decision: str, rationale: str, outcome: str, **kwargs):
        e = LoopReport(message="Main loop iteration",
                       decision=decision, rationale=rationale, outcome=outcome,
                       data=kwargs, kind="loop_report")
        self._write(e)
        self.gov.export_to_model_card(f"Decision: {decision}, Outcome: {outcome}")
        return e.loop_id

# Rule Checker

class RuleChecker:
    """Evaluate runtime decisions against governance rules."""

    def __init__(self, governance: Governance, reporter: Reporter):
        self.gov = governance
        self.reporter = reporter
        self.threats = governance.list_threats()
        self.safety = governance.list_safety_checks()

    def validate_decision(self, decision: str, rationale: str) -> bool:
        for threat in self.threats:
            if threat.lower() in decision.lower():
                self.reporter.report_safety(
                    message=f"Decision violates threat model: {threat}",
                    severity="high",
                    mitigation="blocked",
                    rationale=rationale
                )
                return False
        for check in self.safety:
            if check.lower() in decision.lower():
                self.reporter.report_safety(
                    message=f"Safety rule triggered: {check}",
                    severity="critical",
                    mitigation="halt loop",
                    rationale=rationale
                )
                return False
        return True