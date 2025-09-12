from javu_agi.identity_agent import IdentityAgent
from javu_agi.memory.memory_manager import MemoryManager
from javu_agi.runtime.state_persistence import save_state
import os

def bootstrap():
    os.makedirs("runtime", exist_ok=True)

    identity = IdentityAgent(name="JAVU", traits={
        "curiosity": 0.9,
        "goal_oriented": 0.8,
        "self_preserving": 0.7
    })

    memory = MemoryManager()
    memory.add_memory("Inisialisasi AGI pertama... siap untuk hidup.")

    save_state("identity.pkl", identity)
    save_state("memory.pkl", memory)

    print("✅ Bootstrapping complete. State files saved.")

if __name__ == "__main__":
    bootstrap()
