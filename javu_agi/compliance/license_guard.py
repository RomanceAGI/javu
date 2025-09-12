from __future__ import annotations
from typing import Dict, Any

ALLOW = {"MIT", "BSD", "Apache-2.0", "CC-BY-4.0", "CC-BY-SA-4.0"}
DENY = {"Proprietary-NoRedistribute", "Unknown"}


class LicenseGuard:
    def __init__(self, policy_allow=None, policy_deny=None):
        self.allow = set(policy_allow or ALLOW)
        self.deny = set(policy_deny or DENY)

    def check(self, artifact: Dict[str, Any]) -> (bool, str):
        lic = (artifact or {}).get("license", "Unknown")
        if lic in self.deny:
            return False, "license:deny"
        if self.allow and lic not in self.allow:
            return False, "license:not_whitelisted"
        return True, ""
