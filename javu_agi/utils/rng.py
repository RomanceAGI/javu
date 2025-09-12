import os, random


def seed_everything():
    s = int(os.getenv("AGI_SEED", "0")) or None
    if s is None:
        return
    random.seed(s)
    try:
        import numpy as np

        np.random.seed(s)
    except Exception:
        pass
