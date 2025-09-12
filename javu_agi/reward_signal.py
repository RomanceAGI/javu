from javu_agi.value_model import evaluate_alignment


def compute_reward(insight: str, goal: str, output: str) -> float:
    alignment = evaluate_alignment(output)
    score = 0.0

    if any(kw in output.lower() for kw in ["berhasil", "selesai", "goal tercapai"]):
        score += 1.0
    elif "tidak" in output or "gagal" in output:
        score -= 1.0

    bonus = sum(alignment.values()) / len(alignment)
    return score + bonus
