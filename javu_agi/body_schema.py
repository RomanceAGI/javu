from typing import Dict, Any


class BodySchema:
    """
    Model tubuh & kontrol: kinematika dasar + kontroler.
    """

    def affordances(self, state: Dict[str, Any]):
        return {"graspable": state.get("objects", [])}

    def controller(self, afford, state):
        # Heuristik placeholder: gerak ke objek terdekat
        return {"move_to": state.get("goal_pos", [0, 0, 0])}
