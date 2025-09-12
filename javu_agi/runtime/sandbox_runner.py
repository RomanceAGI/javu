import os
from javu_agi.core_loop import run_user_loop
from javu_agi.goal_memory import get_active_goals
from javu_agi.constraint_checker import enforce_constraints
from javu_agi.memory_pruner import prune_memory
from runtime.user_manager import validate_user


def run_sandbox_session(user_id: str):
    if not validate_user(user_id):
        print(f"[ERROR] Unauthorized user: {user_id}")
        return

    print("=== SANDBOX AGI MODE ===")
    try:
        active_goals = get_active_goals(user_id)
        print("Active Goals:")
        for idx, goal in enumerate(active_goals):
            print(f"[{idx}] {goal}")

        while True:
            prompt = input(">> ")
            if prompt.lower() in ("exit", "quit"):
                break
            output = run_user_loop(user_id, prompt)
            final_output = enforce_constraints(output)
            print(f"\n🤖 JAVU: {final_output}\n")
            prune_memory(user_id)
    except KeyboardInterrupt:
        print("\n[EXIT] Sandbox terminated.")
