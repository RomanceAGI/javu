from javu_agi.goal_planner import generate_plan_from_goal
from javu_agi.llm import call_llm


def detect_plan_failure(response: str) -> bool:
    prompt = f"Apakah teks ini menunjukkan kegagalan rencana? '{response}' Jawab ya atau tidak."
    result = call_llm(prompt).lower()
    return "ya" in result


def generate_alternative_plan(goal_text: str) -> list[str]:
    return generate_plan_from_goal(goal_text).splitlines()
