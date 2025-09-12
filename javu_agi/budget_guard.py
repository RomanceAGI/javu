import json, os, time
# Import configuration constants from the local package rather than a top-level ``config`` module.
from javu_agi.config import BUDGET_DAILY_USD, USAGE_LOG_PATH


# heuristik sangat sederhana (≈4 chars/token)
def estimate_tokens_from_text(text: str) -> int:
    if not text:
        return 0
    return max(1, len(text) // 4)


def _load_usage():
    if os.path.exists(USAGE_LOG_PATH):
        with open(USAGE_LOG_PATH, "r", encoding="utf-8") as f:
            return [json.loads(line) for line in f]
    return []


def _write(line: dict):
    os.makedirs(os.path.dirname(USAGE_LOG_PATH), exist_ok=True)
    with open(USAGE_LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(line) + "\n")


def track_usage(
    model: str,
    prompt_tokens: int,
    completion_tokens: int,
    cost_usd: float,
    user_id: str = "system",
):
    _write(
        {
            "ts": int(time.time()),
            "user": user_id,
            "model": model,
            "prompt_toks": prompt_tokens,
            "completion_toks": completion_tokens,
            "cost_usd": cost_usd,
        }
    )


def get_today_spend_usd():
    logs = _load_usage()
    # naive: all time (cukup untuk guard awal); kalau mau, filter by day
    return sum(x.get("cost_usd", 0.0) for x in logs)


def budget_okay(next_cost_estimate: float) -> bool:
    return (get_today_spend_usd() + next_cost_estimate) <= BUDGET_DAILY_USD
