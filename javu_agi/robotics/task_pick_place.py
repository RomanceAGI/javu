from __future__ import annotations
from typing import Dict, Any
from javu_agi.simulated_env.pybullet_conn import session


def run_pick_place(seed: int = 0) -> Dict[str, Any]:
    # sketch task: load plane + kuka, move joints ke target
    from pybullet_data import getDataPath
    import pybullet as p

    result = {"success": False, "info": {}}
    with session() as sim:
        kuka = sim.load_urdf(
            "kuka", f"{getDataPath()}/kuka_iiwa/model.urdf", base_pos=(0, 0, 0)
        )
        cube = sim.load_urdf(
            "cube", f"{getDataPath()}/cube_small.urdf", base_pos=(0.6, 0, 0.02)
        )
        # naive motion sketch (placeholder) — cukup untuk eval loop
        sim.apply_joint_positions("kuka", list(range(7)), [0, 0.3, 0, -1.2, 0, 1.0, 0])
        for _ in range(600):
            sim.step()
        state = sim.get_state("cube")
        result["success"] = state["pos"][0] > 0.55  # contoh evaluasi sederhana
        result["info"] = state
    return result
