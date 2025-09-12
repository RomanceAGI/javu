from javu_agi.memory.memory import recall_from_memory, save_to_memory


def abstract_from_memory(user_id: str):
    episodes = recall_from_memory(user_id, tag="[EPISODE]")
    rules = [f"Jika {e.lower()}, maka..." for e in episodes if e]
    for rule in rules:
        save_to_memory(user_id, f"[RULE] {rule}")
