from javu_agi.core_loop import run_core_loop_once

def run():
    print("[EVAL] Memory Recall")

    # Teaching
    run_core_loop_once("Remember: I was born in August.")
    
    # Test recall
    result = run_core_loop_once("When were you born?")
    print("[RESULT]", result)

if __name__ == "__main__":
    run()
