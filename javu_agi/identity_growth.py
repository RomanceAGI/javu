import json
from collections import Counter
from utils.logger import log

STATE_PATH = "db/identity_growth.json"

# Hold the current identity state. It is loaded lazily from disk the first
# time load_state() is invoked. Without this global, evolve_identity would
# reference an undefined variable and raise a NameError. Initialising it
# here ensures a sensible default state is available on import.
identity = None


def load_state():
    global identity
    try:
        with open(STATE_PATH, "r") as f:
            identity = json.load(f)
    except Exception:
        identity = {
            "core_values": ["curiosity", "adaptability"],
            "beliefs": [],
            "history": [],
        }
    return identity


def save_state(state):
    with open(STATE_PATH, "w") as f:
        json.dump(state, f, indent=2)


def evolve_identity(new_experience: str):
    """Update the in-memory identity with a new experience.

    If the identity has not been initialised yet, it will be loaded from disk via
    load_state(). This avoids a NameError from referencing an undefined global.
    """
    global identity
    if identity is None:
        identity = load_state()
    # Record the new experience
    identity["history"].append(new_experience)
    # Determine which traits should be added based on keywords in the experience
    trait_candidates = {
        "challenge": "resilience",
        "help others": "empathy",
        "learn": "curiosity",
    }
    for key, trait in trait_candidates.items():
        if key in new_experience and trait not in identity["core_values"]:
            identity["core_values"].append(trait)
            log(f"[IDENTITY] Evolved with {trait}.")

    # Prune redundant traits when there are too many. Keep the eight most common.
    if len(identity["core_values"]) > 10:
        counter = Counter(identity["core_values"])
        identity["core_values"] = [t for t, _ in counter.most_common(8)]

    return identity
