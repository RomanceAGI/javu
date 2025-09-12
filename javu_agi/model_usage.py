PRICES = {
    # OpenAI
    "gpt-5": {"prompt": 0.00001, "completion": 0.00003},
    "gpt-4o": {"prompt": 0.000005, "completion": 0.000015},
    "gpt-5-mini": {"prompt": 0.000002, "completion": 0.000006},
    "gpt-5-nano": {"prompt": 0.0000005, "completion": 0.0000015},
    # Anthropic
    "claude-3-opus": {"prompt": 0.00002, "completion": 0.00006},
    "claude-3-sonnet": {"prompt": 0.000012, "completion": 0.000036},
    "claude-3-haiku": {"prompt": 0.000004, "completion": 0.000012},
    "claude-3-5-sonnet": {"prompt": 0.000014, "completion": 0.000042},
}


def _normalize_model(model: str) -> str:
    if not model:
        return "gpt-4o"
    m = model.lower().strip()
    for key in PRICES.keys():
        if m.startswith(key):
            return key
    return "gpt-4o"


def estimate_cost_usd(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    key = _normalize_model(model)
    p = PRICES.get(model, PRICES["gpt-4o"])
    return prompt_tokens * p["prompt"] + completion_tokens * p["completion"]


def price_profile(model: str) -> dict:
    key = _normalize_model(model)
    return {"model_key": key, **PRICES.get(key, PRICES["gpt-4o"])}
