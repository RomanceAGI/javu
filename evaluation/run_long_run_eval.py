import json
from javu_agi.core_loop import run_user_loop

def load(path="evaluation/long_run_scenarios.json"):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def run():
    user_id = "longrun_eval"
    for case in load():
        print(f"\n🏁 GOAL: {case['prompt']}")
        current_prompt = case["prompt"]
        for i in range(case["turns"]):
            print(f"\n🌀 Turn {i+1}")
            response = run_user_loop(user_id, current_prompt)
            print(f"→ JAVU: {response}")
            current_prompt = response  # next input is previous output

if __name__ == "__main__":
    run()
