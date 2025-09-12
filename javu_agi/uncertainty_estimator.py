def estimate_uncertainty(output: str) -> float:
    """Return estimated confidence level (0.0 to 1.0) based on output language."""
    low_confidence_cues = ["mungkin", "tidak yakin", "kurang tahu", "belum pasti"]
    high_confidence_cues = ["pasti", "jelas", "diketahui", "tanpa ragu"]

    output = output.lower()
    if any(cue in output for cue in low_confidence_cues):
        return 0.3
    elif any(cue in output for cue in high_confidence_cues):
        return 0.9
    return 0.6
    if not output.strip():
        return 0.1
