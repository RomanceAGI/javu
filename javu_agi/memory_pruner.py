import json
import os
from javu_agi.utils.embedding import get_embedding, cosine_similarity
from javu_agi.memory.memory import load_memory, save_memory

PRUNE_LIMIT = 1000
SIMILARITY_THRESHOLD = 0.85


def prune_memory(user_id: str):
    memory = load_memory(user_id)
    if len(memory) <= MAX_MEMORY_LENGTH:
        return False

    # Skor dan sortir
    scored = [(m, score_memory_item(m)) for m in memory]
    scored.sort(key=lambda x: x[1], reverse=True)

    # Top-N + recent
    top_scored = [m for m, _ in scored[:200]]
    recent = memory[-50:]
    new_memory = list(dict.fromkeys(top_scored + recent))  # remove dupe
    save_memory(user_id, new_memory)
    return True

    save_memory(user_id, pruned)
    print(f"[PRUNER] Memori user {user_id} dipangkas → {len(pruned)} item.")


def force_trim_memory(user_id: str, keep_last_n=300):
    memory = load_memory(user_id)
    trimmed = memory[-keep_last_n:]
    save_memory(user_id, trimmed)
    print(f"[PRUNER] Forced trim memori {user_id} → {keep_last_n} terakhir disimpan.")


def score_memory_item(item: str) -> int:
    if "SELF-UPGRADE" in item:
        return 100
    if "REFLECTION" in item:
        return 90
    if "GOAL" in item:
        return 80
    if "ERROR" in item or "FAIL" in item:
        return 70
    return 10  # default rendah
