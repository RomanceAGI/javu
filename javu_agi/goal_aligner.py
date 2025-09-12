from javu_agi.memory.semanticizer import semantic_similarity


def track_goal_context(history: list[str]) -> str:
    return " → ".join([line for line in history if "[GOAL]" in line])


def validate_subgoal_consistency(subgoals: list[str], main_goal: str) -> bool:
    scores = [semantic_similarity(sg, main_goal) for sg in subgoals]
    return all(score > 0.7 for score in scores)
