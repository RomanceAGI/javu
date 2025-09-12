from sentence_transformers import SentenceTransformer
from numpy import dot
from numpy.linalg import norm

try:
    model = SentenceTransformer("all-MiniLM-L6-v2")
except Exception as e:
    model = None
    print("[Embedding Error] Model gagal dimuat:", e)


def get_embedding(text: str):
    if model is None:
        return [0.0] * 384  # dummy fallback
    return model.encode(text)


def cosine_similarity(a, b):
    if not a or not b:
        return 0.0
    return dot(a, b) / (norm(a) * norm(b))
