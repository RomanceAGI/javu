from javu_agi.core_loop import run_core_loop_once

def run():
    print("[EVAL] Goal Achievement")
    input_goal = "Write a short story about a robot"
    result = run_core_loop_once(input_goal)
    print("[RESULT]", result)

if __name__ == "__main__":
    run()

