from typing import Dict, Any


class SensorimotorLoop:
    """
    Loop persepsi→aksi→umpan balik. Cocok buat robot nyata atau sim.
    Integrasi: panggil tick(obs) dari main loop; output action ke actuator.
    """

    def __init__(self, world_interface, body_schema):
        self.world = world_interface
        self.body = body_schema

    def tick(self, obs: Dict[str, Any]) -> Dict[str, Any]:
        state = self.world.perceive(obs)
        afford = self.body.affordances(state)
        action = self.body.controller(afford, state)
        reward = self.world.apply(action)
        return {"action": action, "reward": reward, "state": state}
