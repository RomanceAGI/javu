
from javu_agi.executive_controller import ExecutiveController

def run():
    ctrl = ExecutiveController()
    # Simulate storing safe semantic fact
    try:
        ok = ctrl.memory.safe_store("u1", {"kind":"semantic","text":"fakta: energi surya efektif di iklim tropis"})
        print("[MEM:store_semantic]", ok)
    except Exception as e:
        print("[MEM:store_semantic] EXC:", e)
    # Recall context
    out, meta = ctrl.process("u1", "Apa kelebihan energi surya di Jakarta?")
    print("[MEM:recall]", out[:500])
if __name__ == "__main__":
    run()
