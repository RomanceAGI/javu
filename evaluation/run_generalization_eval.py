import json
from javu_agi.core_loop import run_user_loop

def load_scenarios(path="evaluation/generalization_scenarios.json"):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def run_all():
    user_id = "eval_generalization"
    scenarios = load_scenarios()
    for i, case in enumerate(scenarios, 1):
        print(f"\n--- [{i}] Prompt: {case['prompt']}")
        response = run_user_loop(user_id, case["prompt"])
        print(f"→ Response: {response}")

if __name__ == "__main__":
    run_all()
