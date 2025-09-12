def score_plan(world, prompt: str, steps) -> float:
    try:
        txt = "\n".join(f"{s.get('tool','')} {s.get('cmd','')}" for s in (steps or []))
        return float(world.value_estimate(prompt, txt))
    except Exception:
        return 0.0
