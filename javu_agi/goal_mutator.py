import random
from javu_agi.utils.embedding import get_embedding, cosine_similarity


def mutate_goal(goal: str) -> list[str]:
    verbs = ["optimalkan", "eksplorasi", "evaluasi", "tingkatkan", "integrasi"]
    mutations = []

    for _ in range(5):
        verb = random.choice(verbs)
        mutated = f"{verb} {goal}"
        if mutated != goal:
            mutations.append(mutated)
    return mutations


def score_goal_mutation(original: str, mutated: str) -> float:
    o_vec = get_embedding(original)
    m_vec = get_embedding(mutated)
    return cosine_similarity(o_vec, m_vec)


def generate_best_mutations(goal: str, top_n: int = 3) -> list[str]:
    candidates = mutate_goal(goal)
    scored = [(g, score_goal_mutation(goal, g)) for g in candidates]
    scored.sort(key=lambda x: x[1], reverse=True)
    return [g for g, _ in scored[:top_n]]
