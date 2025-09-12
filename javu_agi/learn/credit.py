import json
from pathlib import Path
from collections import defaultdict


class CreditAssigner:
    def __init__(self, trace_dir="trace", reward_dir="rewards"):
        self.trace_dir = Path(trace_dir)
        self.reward_dir = Path(reward_dir)

    def assign(self):
        node_rewards = defaultdict(float)
        for reward_file in self.reward_dir.glob("*.json"):
            reward_data = json.load(open(reward_file))
            episode_id = reward_data.get("episode_id")
            reward_val = reward_data.get("reward", 0)
            trace_file = self.trace_dir / f"{episode_id}.jsonl"
            if trace_file.exists():
                for line in open(trace_file):
                    node = json.loads(line)
                    node_rewards[node["id"]] += reward_val / max(1, len(node_rewards))
        return node_rewards
