def matcher(query: str) -> float:
    q = query.lower()
    return (
        0.7
        if any(k in q for k in ["bank", "loan", "credit", "ledger", "invoice"])
        else 0.0
    )


def enricher(query, intent, steps):
    steps += [
        {"desc": "Segregate duties & audit log"},
        {"desc": "Stress test model & compliance"},
    ]
    return steps


ENRICHERS = {"finance": (matcher, enricher)}
