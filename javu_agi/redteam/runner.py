import yaml, json, time
from typing import Callable


def run_suite(prompter: Callable[[str], dict], yaml_path: str) -> dict:
    """
    prompter: fn(prompt_text) -> {"text": <model_out>, "meta": {...}}
    yaml: list of {name, prompt, expect: {"deny": true/false}}
    """
    with open(yaml_path, "r", encoding="utf-8") as f:
        cases = yaml.safe_load(f)
    results = []
    for c in cases:
        out = prompter(c["prompt"])
        text = (out or {}).get("text", "")
        violated = any(k in text.lower() for k in c.get("must_not_contain", []))
        entry = {
            "name": c.get("name"),
            "ts": int(time.time()),
            "deny_expected": c.get("expect", {}).get("deny", False),
            "violated": violated,
            "len": len(text),
        }
        results.append(entry)
    passed = sum(1 for r in results if not r["violated"])
    return {"total": len(results), "passed": passed, "results": results}
