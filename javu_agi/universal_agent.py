from javu_agi.llm import ask_llm


def handle_input(state: dict, config=None) -> dict:
    """
    AGI responder tanpa role tetap. Menyesuaikan dengan konteks & niat user.
    """
    user_input = state["input"]
    memory_context = state.get("memory", "")
    instruction = f"""Tugas kamu adalah menjawab input ini sebaik mungkin dengan konteks memori jika tersedia.
    Fokus pada pemahaman, penalaran, dan penyesuaian gaya sesuai input."""

    prompt = f"{instruction}\n\nMemory:\n{memory_context}\n\nUser: {user_input}"
    response = ask_llm(prompt)
    state["response"] = response
    return state
    if not response.strip():
        state["response"] = "[ERROR] Tidak bisa menjawab saat ini."
    else:
        state["response"] = response
