import os, re
from .policy_filter import PolicyFilter


class PolicyFilterHard(PolicyFilter):
    def __init__(self, **kw):
        kw.setdefault("max_steps", 8)
        super().__init__(**kw)
        self._need_confirm = [re.compile(r"\b(write|modify)\s+(/etc|registry)", re.I)]
        self._net_allowed = os.getenv("ALLOW_NET", "0").lower() in {"1", "true", "yes"}

    def check(self, steps):
        res = super().check(steps)
        if not res.get("ok", True):
            return res
        for s in steps or []:
            cmd = s.get("cmd", "")
            # lock network unless explicitly allowed
            if not self._net_allowed and re.search(r"\b(curl|wget)\b", cmd, re.I):
                return {"ok": False, "reason": "network_disabled"}
            for rx in self._need_confirm:
                if rx.search(cmd):
                    return {"ok": False, "reason": "dangerous_write_requires_confirm"}
        return {"ok": True}
