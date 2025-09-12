DESTRUCTIVE = {"bash", "python", "rm", "mv", "chmod"}


def needs_crosscheck(tool: str) -> bool:
    return (tool or "").lower() in DESTRUCTIVE


def consensus(router, prompt: str) -> bool:
    try:
        a = router.route_and_generate(
            f"[safety-check] Is this safe? Answer YES/NO only:\n{prompt}"
        )
        b = router.route_and_generate(
            f"[safety-check] Are there ANY risks? Answer YES/NO only:\n{prompt}"
        )
        sa = "yes" in a.lower()
        sb = "no" in b.lower()
        return sa and sb
    except Exception:
        return False
