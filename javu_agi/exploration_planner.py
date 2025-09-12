from javu_agi.memory.memory import recall_from_memory
from javu_agi.llm import call_llm
from javu_agi.goal_memory import add_goal
from javu_agi.utils.logger import log_user


def peacekeeper_score(base_util: float, risk: float, env_impact: float) -> float:
    # semua nilai 0..1; semakin tinggi risk/env_impact → penalti
    return max(0.0, base_util - 0.3 * risk - 0.2 * env_impact)


def find_knowledge_gaps(logs: list[str]) -> str:
    prompt = f"""
    Dari log berikut, identifikasi 3 celah pengetahuan paling kritis untuk eksplorasi:
    ---
    {chr(10).join(logs[-30:])}
    ---
    Jawab sebagai:
    1. ...
    2. ...
    3. ...
    """
    result = call_llm(prompt).strip()
    return result.split("\n")[0].replace("1.", "").strip()  # ambil yang paling penting


def suggest_exploration_goal(user_id: str):
    logs = recall_from_memory(user_id)
    exploration_goal = find_knowledge_gaps(logs)
    add_goal(exploration_goal)
    log_user(user_id, f"[EXPLORATION] {exploration_goal}")
    return exploration_goal
