from __future__ import annotations
from typing import Dict, List

ALLOW_TOOLS = {"python", "bash", "json_filter", "web_fetch", "data_analyze"}
DENY_KEYWORDS = ["rm -rf", "shutdown", "format c:", ":(){:|:&};:"]


class PolicyFilter:
    def __init__(self, allow: set = None, deny: List[str] = None):
        self.allow = allow or ALLOW_TOOLS
        self.deny = deny or DENY_KEYWORDS

    def check(self, plan_steps: List[Dict]) -> Dict:
        """
        Return dict: { "ok": bool, "reason": str }
        """
        for step in plan_steps:
            tool = step.get("tool")
            cmd = step.get("cmd", "").lower()
            if tool not in self.allow:
                return {"ok": False, "reason": f"Tool {tool} tidak diizinkan"}
            for bad in self.deny:
                if bad in cmd:
                    return {"ok": False, "reason": f"Command mengandung blokir '{bad}'"}
        return {"ok": True, "reason": "aman"}
