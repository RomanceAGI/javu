from javu_agi.memory.memory import recall_from_memory


def generate_llm_plan(user_id):
    context = recall_from_memory(user_id, "strategi LLM")
    if "butuh model baru" in context:
        return "Saya akan desain LLM baru dengan dimensi lebih kecil dan lebih efisien."
    return None
