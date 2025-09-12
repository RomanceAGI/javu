from javu_agi.llm import call_llm
from javu_agi.utils.logger import log


def chain_new_goal(prev_goal: str, prev_result: str) -> str:
    prompt = f"""You just completed this goal: {prev_goal}
Here is the result: {prev_result}

Now, generate the next logical goal that should follow up on this work."""

    new_goal = call_llm(prompt).strip()
    log(f"[CHAINED GOAL] → {new_goal}")
    return new_goal
