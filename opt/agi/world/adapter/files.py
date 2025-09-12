def value_estimate(prompt, cmd, **kw):
    return 0.65
def simulate_action(x, **kw):
    risky = any(k in cmd.lower() for k in ["rm -rf", "/etc/", "/root/"])
    return {"risk_level": "high" if risky else "low", "expected_confidence": 0.6}
