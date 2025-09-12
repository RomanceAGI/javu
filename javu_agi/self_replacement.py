from javu_agi.memory.memory import recall_from_memory
from javu_agi.llm_router import switch_llm_model
from javu_agi.utils.logger import log_user


def maybe_replace_llm(user_id):
    memory = recall_from_memory(user_id, "performansi")
    if any(k in memory for k in ["buruk", "lambat", "salah"]):
        switch_llm_model(user_id, "local-model-v2")
        log_user(user_id, "[SELF_REPLACEMENT] Ganti LLM → local-model-v2 (fallback)")
    else:
        log_user(user_id, "[SELF_REPLACEMENT] LLM stabil.")
