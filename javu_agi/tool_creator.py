from javu_agi.llm import call_llm
from javu_agi.utils.logger import log_user


def generate_tool_concept(user_input: str) -> str:
    prompt = f"""
Buat konsep tool/alat AI berdasarkan ide ini:

\"\"\"{user_input}\"\"\"

Berikan penjelasan singkat: fungsi, input, output, dan contoh penggunaannya.
"""
    result = call_llm(prompt)
    log_user("system", f"[TOOL CONCEPT] {user_input} → {result[:200]}")
    return result
