from javu_agi.executive_controller import ExecutiveController

def run():
    ctrl = ExecutiveController()
    out, meta = ctrl.process("user-1", "mm: ringkas visual+voice untuk proposal efisiensi energi gedung pemerintah")
    print("[MM]", out[:1000])
if __name__ == "__main__":
    run()
