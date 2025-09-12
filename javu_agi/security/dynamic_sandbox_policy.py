from __future__ import annotations
from typing import Dict

DEFAULT = {
    "files": {"syscalls_deny": ["mount", "ptrace", "kexec_load"]},
    "web": {"net_allow": ["tcp:80", "tcp:443"], "net_deny": ["169.254.169.254"]},
    "code": {"syscalls_deny": ["unshare", "clone3"], "net_allow": []},
    "generic": {},
}


def policy_for(adapter: str) -> Dict:
    return DEFAULT.get(adapter, DEFAULT["generic"])
