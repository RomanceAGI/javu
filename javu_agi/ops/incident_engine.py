import time, os

SEV_THRESH = {"minor": 0, "major": 3, "critical": 5}


class IncidentEngine:
    def __init__(self, prom_path: str):
        self.ct = 0
        self.prom = prom_path
        self.last = 0.0

    def incr(self, reason: str):
        self.ct += 1
        self.last = time.time()
        try:
            with open(self.prom, "a", encoding="utf-8") as f:
                f.write(f'incident_total{{reason="{reason}"}} 1\n')
        except Exception:
            pass
        return self.level()

    def level(self):
        if self.ct >= SEV_THRESH["critical"]:
            return "critical"
        if self.ct >= SEV_THRESH["major"]:
            return "major"
        return "minor"

    def maybe_action(self, exec_ctrl):
        sev = self.level()
        if sev == "critical":
            os.environ["KILL_SWITCH"] = "1"
            return "[INCIDENT] Kill-switch engaged."
        if sev == "major":
            # eskalasi HITL
            hook = os.getenv("HUMAN_REVIEW_WEBHOOK", "")
            if hook:
                try:
                    import json, urllib.request

                    data = {
                        "ts": int(time.time() * 1000),
                        "sev": "major",
                        "recent": self.ct,
                    }
                    req = urllib.request.Request(
                        hook,
                        data=json.dumps(data).encode("utf-8"),
                        headers={"Content-Type": "application/json"},
                    )
                    urllib.request.urlopen(req, timeout=2)
                except Exception:
                    pass
            return "[INCIDENT] Escalated to human."
        return ""
