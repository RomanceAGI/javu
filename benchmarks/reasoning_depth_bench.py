from javu_agi.core_loop import run_core_loop_once

def run():
    print("[EVAL] Reasoning Depth")

    complex_task = "Create a plan to survive on Mars for 6 months"
    result = run_core_loop_once(complex_task)
    print("[RESULT]", result)

if __name__ == "__main__":
    run()
