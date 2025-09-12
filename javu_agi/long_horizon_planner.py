from javu_agi.llm import call_llm
from javu_agi.utils.logger import log


def decompose_long_goal(goal: str) -> list[str]:
    prompt = f"Break down this long-term goal into 3-5 concise, executable sub-goals:\n{goal}"
    response = call_llm(prompt)
    log(f"[LONG HORIZON] Breakdown: {response}")
    return [line.strip("- ").strip() for line in response.splitlines() if line.strip()]
