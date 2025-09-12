from __future__ import annotations
from typing import Dict, Any, Tuple
from javu_agi.tools.tool_contracts import ContractRegistry, ToolContract
import json


class ContractViolation(Exception): ...


class ContractVerifier:
    def __init__(self, registry: ContractRegistry):
        self.reg = registry

    def precheck(self, tool: str, args: Dict[str, Any]) -> Tuple[bool, str]:
        c: ToolContract = self.reg.get(tool) or ToolContract(tool)
        for fn in c.preconditions:
            try:
                if not fn(args):
                    if audit:
                        audit.append(
                            "contract_violation", {"tool": tool, "phase": "pre"}
                        )
                    return False, "precondition"
            except Exception:
                if audit:
                    audit.append("contract_error", {"tool": tool, "phase": "pre"})
                return False, "precondition_error"
        return True, ""

    def postcheck(self, tool: str, result: Dict[str, Any]) -> Tuple[bool, str]:
        c: ToolContract = self.reg.get(tool) or ToolContract(tool)
        if len((result.get("stdout", "") or "").encode()) > c.max_output_bytes:
            return False, "output_too_large"
        for fn in c.postconditions:
            try:
                if not fn(result):
                    return False, "postcondition"
            except Exception:
                return False, "postcondition_error"
        return True, ""
