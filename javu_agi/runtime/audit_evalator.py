import json
import os
from datetime import datetime

REWARD_LOG_PATH = "trace/reward_log.json"
MEMORY_PATH = "memory"


def load_reward_log():
    if not os.path.exists(REWARD_LOG_PATH):
        return []
    with open(REWARD_LOG_PATH, "r") as f:
        return json.load(f)


def list_memory_files():
    return [f for f in os.listdir(MEMORY_PATH) if f.endswith(".json")]


def summarize_rewards(log):
    if not log:
        return "No rewards logged."
    values = [r["value"] for r in log]
    return {
        "total_steps": len(values),
        "average_reward": sum(values) / len(values),
        "min_reward": min(values),
        "max_reward": max(values),
    }


def evaluate():
    print("[🧾] Reward Summary")
    rewards = load_reward_log()
    print(json.dumps(summarize_rewards(rewards), indent=2))

    print("\n[🧠] Memory Files")
    for f in list_memory_files():
        path = os.path.join(MEMORY_PATH, f)
        size = os.path.getsize(path)
        ts = datetime.fromtimestamp(os.path.getmtime(path))
        print(f"- {f} ({round(size / 1024, 2)} KB, updated {ts})")


if __name__ == "__main__":
    evaluate()
