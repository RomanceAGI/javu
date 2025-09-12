from __future__ import annotations
from typing import Dict, Any


class EmbodiedIntegrator:
    """
    Menjembatani world.observe() -> sensorimotor.tick() -> memory.store(),
    plus eksekusi satu aksi aman (jika ada).
    """

    def __init__(self, world, body, sensorimotor, memory, guard):
        self.world, self.body, self.sensorimotor = world, body, sensorimotor
        self.memory, self.guard = memory, guard

    def cycle(self):
        try:
            obs = self.world.observe()
            state = self.sensorimotor.tick(obs)
            self.memory.store("sensorimotor", state)
            return {"status": "ok", "state": state}
        except Exception as e:
            return {"status": "err", "err": str(e)}

    def maybe_act(self, safe_cmd: str | None = None):
        if not safe_cmd:
            return {"acted": False}
        # ACL / governor tetap di guard di luar; di sini hanya logging
        try:
            self.body.apply(safe_cmd)  # jika ada shim
            return {"acted": True, "cmd": safe_cmd}
        except Exception:
            return {"acted": False}
