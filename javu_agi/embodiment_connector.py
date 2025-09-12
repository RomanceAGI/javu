from __future__ import annotations
import os, threading, time
from typing import Any, Dict, Callable


class ActuatorBus:
    def __init__(self) -> None:
        self.devices: Dict[str, Callable[[Dict[str, Any]], Dict[str, Any]]] = {}
        self.safe = True
        self.hitl = os.getenv("HITL_REQUIRED", "1") == "1"
        self.last_result: Dict[str, Any] = {}

    def register(
        self, name: str, driver: Callable[[Dict[str, Any]], Dict[str, Any]]
    ) -> None:
        self.devices[name] = driver

    def send(self, name: str, action: Dict[str, Any]) -> Dict[str, Any]:
        if self.safe is False:
            raise RuntimeError("actuator bus locked")
        if self.hitl and not action.get("approved_by_human"):
            raise RuntimeError("human approval required")
        d = self.devices.get(name)
        if not d:
            raise RuntimeError("device not found")
        self.last_result = d(dict(action))
        return dict(self.last_result)

    def lock(self) -> None:
        self.safe = False

    def unlock(self) -> None:
        self.safe = True

    def heartbeat(self, name: str, interval_s: float = 5.0) -> None:
        def _hb():
            while True:
                time.sleep(interval_s)

        t = threading.Thread(target=_hb, daemon=True)
        t.start()


BUS = ActuatorBus()
