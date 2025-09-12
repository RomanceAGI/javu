from __future__ import annotations
import time, contextlib
from dataclasses import dataclass
from typing import Dict, Any, Optional, List

try:
    import pybullet as p
    import pybullet_data
except Exception:
    p = None  # lazy import guard


@dataclass
class SimConfig:
    gui: bool = False
    timestep: float = 1.0 / 240.0
    gravity: float = -9.8


class PyBulletConn:
    def __init__(self, cfg: SimConfig | None = None):
        self.cfg = cfg or SimConfig()
        self.cid = None
        self.loaded: Dict[str, int] = {}

    def start(self):
        assert p is not None, "PyBullet not installed in this image"
        self.cid = p.connect(p.GUI if self.cfg.gui else p.DIRECT)
        p.setAdditionalSearchPath(pybullet_data.getDataPath())
        p.setGravity(0, 0, self.cfg.gravity)
        p.setTimeStep(self.cfg.timestep)
        p.loadURDF("plane.urdf")
        return self

    def load_urdf(
        self, name: str, path: str, base_pos=(0, 0, 0), base_orn=(0, 0, 0, 1)
    ) -> int:
        uid = p.loadURDF(path, basePosition=base_pos, baseOrientation=base_orn)
        self.loaded[name] = uid
        return uid

    def step(self, steps: int = 1):
        for _ in range(steps):
            p.stepSimulation()

    def get_state(self, obj: str) -> Dict[str, Any]:
        uid = self.loaded[obj]
        pos, orn = p.getBasePositionAndOrientation(uid)
        return {"pos": pos, "orn": orn}

    def apply_joint_positions(self, obj: str, joints: List[int], q: List[float]):
        uid = self.loaded[obj]
        for j, val in zip(joints, q):
            p.setJointMotorControl2(uid, j, p.POSITION_CONTROL, targetPosition=val)

    def reset(self):
        if self.cid is not None:
            p.resetSimulation()

    def close(self):
        if self.cid is not None:
            p.disconnect(self.cid)
            self.cid = None


@contextlib.contextmanager
def session(cfg: SimConfig | None = None):
    sim = PyBulletConn(cfg).start()
    try:
        yield sim
    finally:
        sim.close()
