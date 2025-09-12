def should_reflect(confidence: float, threshold: float = 0.5) -> bool:
    return confidence < threshold


def should_ask_human(confidence: float, critical: bool = False) -> bool:
    return confidence < 0.4 or (critical and confidence < 0.7)
