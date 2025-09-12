import os


def risky(world, state_text: str, tool: str, cmd: str) -> bool:
    try:
        pred = world.mb.predict(state_text, f"{tool} {cmd}")
        thr = float(os.getenv("RISK_MAX", "0.55"))
        return float(pred.get("risk", 1.0)) > thr
    except Exception:
        return False
