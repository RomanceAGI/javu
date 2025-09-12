WORLD_STATE = {
    "agent_location": "room1",
    "object": "box",
    "box_location": "table",
}


def apply_action(action: str) -> dict:
    """Simulate action and update world state."""
    if action == "move box to floor":
        WORLD_STATE["box_location"] = "floor"
    elif action == "move to room2":
        WORLD_STATE["agent_location"] = "room2"
    return WORLD_STATE.copy()


def get_world_state() -> dict:
    return WORLD_STATE.copy()


WORLD_LOG = []


def apply_action(action: str) -> dict:
    ...
    WORLD_LOG.append(f"{action} → {WORLD_STATE.copy()}")
    return WORLD_STATE.copy()


def get_trace() -> list[str]:
    return WORLD_LOG.copy()
