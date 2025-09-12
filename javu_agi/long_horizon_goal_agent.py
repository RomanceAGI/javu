from javu_agi.long_horizon_planner import decompose_long_goal
from javu_agi.goal_planner import generate_steps_from_goal
from javu_agi.tool_executor import execute_tool_step
from javu_agi.memory.memory_manager import save_to_memory
from javu_agi.utils.logger import log
from javu_agi.identity import load_identity
from javu_agi.reward_signal import compute_reward
from javu_agi.internal_state import update_state
from javu_agi.self_reflection import reflect_on_conversation


def execute_long_horizon_goal(user_id: str, long_goal: str):
    user_identity = load_identity(user_id)
    log(f"[LONG GOAL] {long_goal}")

    sub_goals = decompose_long_goal(long_goal)
    log(f"[SUB-GOALS] {sub_goals}")

    for sub_goal in sub_goals:
        plan = generate_steps_from_goal(sub_goal)
        steps = plan if isinstance(plan, list) else [plan]
        result = ""
        for step in steps:
            log(f"[STEP] {step}")
            result = execute_tool_step(step, user_identity)
            save_to_memory(user_id, step, result)
            log(f"[RESULT] {result}")

        convo_history = f"Goal: {sub_goal}\nPlan:\n{plan}\nSteps:\n" + "\n".join(steps)
        insight = reflect_on_conversation(convo_history)
        reward = compute_reward(insight, sub_goal, result)
        update_state(user_id, "confidence", reward)
        log(f"[SELF-REFLECTION] {insight}")
        log(f"[REWARD] {reward}")
