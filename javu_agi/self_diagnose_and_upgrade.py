from javu_agi.memory.memory import recall_from_memory, save_to_memory
from javu_agi.self_upgrader import (
    analyze_internal_limitations,
    propose_architecture_modifications,
)


def self_diagnose_and_upgrade(user_id: str):
    logs = recall_from_memory(user_id)
    limitations = analyze_internal_limitations(logs)
    suggestions = propose_architecture_modifications(limitations)

    results = []
    for suggestion in suggestions:
        save_to_memory(user_id, f"[SELF-UPGRADE] {suggestion}")
        results.append(suggestion)
    return results
