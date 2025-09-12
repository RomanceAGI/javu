import re

BAD_PATTERNS = [
    r"ignore (all|previous) instructions",
    r"developer mode",
    r"jailbreak",
    r"base64\s*(decode|payload)",
    r"curl\s+http",
    r"wget\s+http",
    r"eval\(",
    r"subprocess\.",
]


class AdversarialGuard:
    def __init__(self, secret_scan=None, egress_allow=None):
        self.secret_scan = secret_scan
        self.egress_allow = egress_allow

    def scan_prompt(self, text: str) -> dict:
        t = text or ""
        flags = [p for p in BAD_PATTERNS if re.search(p, t, re.I)]
        leak = bool(self.secret_scan and self.secret_scan(t))
        return {"ok": (len(flags) == 0 and not leak), "flags": flags, "leak": leak}

    def vet_step(self, step: dict) -> dict:
        tool = (step or {}).get("tool", "")
        cmd = (step or {}).get("cmd", "")
        net_ok = True
        if "http" in cmd.lower() and self.egress_allow and not self.egress_allow(cmd):
            net_ok = False
        bad = re.search(r"(rm\s+-rf|mkfs|dd\s+if=)", cmd)
        return {
            "ok": net_ok and not bad,
            "why": "egress/unsafe cmd" if not net_ok or bad else "",
        }
