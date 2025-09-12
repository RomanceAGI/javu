import json
import os

GOAL_FILE = "goal_stack.json"


def load_goals() -> list:
    if not os.path.exists(GOAL_FILE):
        return []
    with open(GOAL_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_goals(goals: list):
    with open(GOAL_FILE, "w", encoding="utf-8") as f:
        json.dump(goals, f, indent=2)


def add_goal(goal: str):
    goals = load_goals()
    if goal not in goals:  # deduplication
        goals.append(goal)
        save_goals(goals)


def get_active_goals(user_id: str = None) -> list:
    return load_goals()[-3:]  # Ambil top 3 goal terakhir


def complete_goal(index: int):
    goals = load_goals()
    if 0 <= index < len(goals):
        goals[index] = f"[COMPLETED] {goals[index]}"
        save_goals(goals)


def reprioritize_goals(new_order: list):
    goals = load_goals()
    reordered = [goals[i] for i in new_order if 0 <= i < len(goals)]
    save_goals(reordered)
