import os, pickle

DATA_DIR = os.getenv("DATA_DIR", "/data")
RUNTIME_DIR = os.getenv("RUNTIME_DIR", os.path.join(DATA_DIR, "runtime"))
os.makedirs(RUNTIME_DIR, exist_ok=True)


def _path(filename: str) -> str:
    return os.path.join(RUNTIME_DIR, filename)


def save_state(filename, obj):
    with open(_path(filename), "wb") as f:
        pickle.dump(obj, f)


def load_state(filename):
    try:
        with open(_path(filename), "rb") as f:
            return pickle.load(f)
    except FileNotFoundError:
        return None
