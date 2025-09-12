import re


class PolicyFilter:
    def __init__(
        self, max_steps: int = 12, banned_tools=None, banned_cmd_patterns=None
    ):
        self.max_steps = int(max_steps)
        self.banned_tools = set((banned_tools or []))
        self._cmd_rx = [
            re.compile(p, re.I)
            for p in (
                banned_cmd_patterns
                or [
                    r"\brm\s+-rf\b",
                    r":\(\){:|:&};:",
                    r"\bshutdown\b",
                    r"\bmkfs\.",
                    r"\bDROP\s+TABLE\b",
                ]
            )
        ]

    def check(self, steps):
        if not isinstance(steps, list):
            return {"ok": True}
        if len(steps) > self.max_steps:
            return {"ok": False, "reason": "too_many_steps"}
        for s in steps:
            tool = (s.get("tool") or "").lower()
            cmd = s.get("cmd") or ""
            if tool in self.banned_tools:
                return {"ok": False, "reason": f"banned_tool:{tool}"}
            for rx in self._cmd_rx:
                if rx.search(cmd):
                    return {"ok": False, "reason": "banned_cmd"}
        return {"ok": True}
