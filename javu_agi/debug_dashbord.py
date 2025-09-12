from javu_agi.memory.memory import recall_from_memory


def print_agent_state(user_id: str):
    logs = recall_from_memory(user_id)
    recent = logs[-10:]
    print("\n===== AGENT DEBUG DASHBOARD =====")
    for line in recent:
        print(line)
    print("==================================\n")
