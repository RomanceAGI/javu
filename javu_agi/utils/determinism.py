import os, random, hashlib, numpy as np


def set_seed(trace_id: str):
    """Set global RNG seed deterministically based on trace_id"""
    h = hashlib.sha256(trace_id.encode()).hexdigest()
    seed = int(h[:8], 16)  # pakai 32 bit dari hash
    random.seed(seed)
    np.random.seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)
    return seed
