from javu_agi.uncertainty_estimator import estimate_uncertainty


def must_verify(output: str, critical: bool = False) -> bool:
    conf = estimate_uncertainty(
        output
    )  # returns 0..1 (semantik terbalik di file lama; treat as confidence)
    thr = 0.5 if not critical else 0.8
    return conf < thr
