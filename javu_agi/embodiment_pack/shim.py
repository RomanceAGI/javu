from __future__ import annotations
from typing import Dict, Any, Optional

from javu_agi.tools.registry import ToolRegistry, ToolError


class SensorHub:
    def __init__(self, tools: ToolRegistry):
        self.tools = tools

    def read_text(self, source: str, **kw) -> str:
        # placeholder: could call a safe fetch tool or local file reader
        return kw.get("text", "")


class ActuatorHub:
    def __init__(self, tools: ToolRegistry):
        self.tools = tools

    def run_python(self, code: str) -> Dict[str, Any]:
        return self.tools.run("python_inline", {"code": code})

    def summarize(self, text: str, n: int = 2) -> Dict[str, Any]:
        return self.tools.run("summarize", {"text": text, "max_sentences": n})


class Embodiment:
    """High-level shim to group sensors/actuators (non-robotic for now)."""

    def __init__(self, tools: ToolRegistry):
        self.sensors = SensorHub(tools)
        self.acts = ActuatorHub(tools)
