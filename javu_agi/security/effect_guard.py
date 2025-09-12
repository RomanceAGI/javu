import re
from dataclasses import dataclass
from typing import Dict


@dataclass
class EffectPolicy:
    read_fs: bool = True
    write_fs: bool = False
    exec_proc: bool = False
    net_egress: bool = False


# default kebijakan minimal untuk tool umum (override via TOOL_EFFECTS_JSON bila perlu)
DEFAULTS: Dict[str, EffectPolicy] = {
    "bash": EffectPolicy(
        read_fs=True, write_fs=False, exec_proc=True, net_egress=False
    ),
    "python": EffectPolicy(
        read_fs=True, write_fs=False, exec_proc=True, net_egress=False
    ),
    "browser": EffectPolicy(
        read_fs=False, write_fs=False, exec_proc=False, net_egress=True
    ),
    "web": EffectPolicy(
        read_fs=False, write_fs=False, exec_proc=False, net_egress=True
    ),
    "git": EffectPolicy(read_fs=True, write_fs=True, exec_proc=True, net_egress=True),
    "files": EffectPolicy(
        read_fs=True, write_fs=True, exec_proc=False, net_egress=False
    ),
    "generic": EffectPolicy(),
}

_RX_WRITE = re.compile(r"\b(mv|rm|cp|touch|echo\s+.+\s*>>|tee|sed\s+-i)\b", re.I)
_RX_EXEC = re.compile(
    r"\b(python|node|npm|pip|bash|sh|-c\s|/bin/|subprocess|exec\()", re.I
)
_RX_NET = re.compile(r"\b(curl|wget|http://|https://|git\s+clone)\b", re.I)


def _infer_effects(cmd: str):
    t = cmd or ""
    return {
        "write_fs": bool(_RX_WRITE.search(t)),
        "exec_proc": bool(_RX_EXEC.search(t)),
        "net_egress": bool(_RX_NET.search(t)),
    }


class EffectGuard:
    def __init__(self, policy_overrides: Dict[str, EffectPolicy] | None = None):
        self.p = {**DEFAULTS, **(policy_overrides or {})}

    def check(self, tool: str, cmd: str) -> (bool, str):
        pol = self.p.get((tool or "").lower(), DEFAULTS.get("generic"))
        eff = _infer_effects(cmd)
        if eff["write_fs"] and not pol.write_fs:
            return False, "write_fs_denied"
        if eff["exec_proc"] and not pol.exec_proc:
            return False, "exec_proc_denied"
        if eff["net_egress"] and not pol.net_egress:
            return False, "net_egress_denied"
        if audit and not all(v == "ok" for v in (pol, eff)):
            audit.append("effect_violation", {"tool": tool, "cmd": cmd, "eff": eff})
        return True, "ok"
