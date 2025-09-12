from javu_agi.identity import load_identity
from javu_agi.memory.memory import recall_from_memory, update_memory_from_interaction
from javu_agi.llm import call_llm


def run_user_loop(user_id, user_input):
    identity = load_identity(user_id)
    context = recall_from_memory(user_id, user_input)

    prompt = f"""
Nama: {identity.get('name')}
Peran: {identity.get('role')}
Memory Terkait:
{context}

User: {user_input}
JAVU:"""

    output = call_llm(prompt)
    update_memory_from_interaction(user_id, user_input, output)
    return output
