from javu_agi.utils.embedding import get_embedding, cosine_similarity
import time

memory_db = {}  # in-memory cache {user_id: [(text, embedding, timestamp)]}
MAX_ITEMS = 500
SIM_THRESHOLD = 0.9
DECAY_TIME = 86400  # 1 day


def store_memory(user_id: str, text: str):
    global memory_db
    emb = get_embedding(text)
    timestamp = time.time()

    if user_id not in memory_db:
        memory_db[user_id] = []

    # Drop if too similar
    for existing_text, vec, ts in memory_db[user_id]:
        if cosine_similarity(vec, emb) > SIM_THRESHOLD:
            return False

    memory_db[user_id].append((text, emb, timestamp))
    memory_db[user_id] = prune(user_id)
    return True


def prune(user_id: str):
    current = memory_db[user_id]
    now = time.time()
    # Aging decay + max length
    aged = [(txt, vec, ts) for txt, vec, ts in current if (now - ts) < DECAY_TIME]
    return aged[-MAX_ITEMS:]
