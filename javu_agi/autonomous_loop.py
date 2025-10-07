import os, time
from typing import List

from javu_agi.identity import load_identity
from javu_agi.intrinsic_drive import generate_intrinsic_goal
from javu_agi.hierarchical_planner import plan_with_checks
from javu_agi.policy_enforcer import check_text_action, allow_tool
from javu_agi.tool_executor import execute_tool, react_tool_chain
from javu_agi.replanner import detect_plan_failure, generate_alternative_plan
from javu_agi.self_reflection import reflect_on_conversation
from javu_agi.reward_signal import compute_reward
from javu_agi.world_model import WorldModel
from javu_agi.continual_learner import (
    ingest_experience,
    consolidate_knowledge,
    update_policy_from_reflection,
)
from javu_agi.critic_verifier import approve, critique
from javu_agi.tool_rl_bandit import EpsilonGreedyBandit

try:
    from trace.trace_logger import log_trace
except Exception:

    def log_trace(uid, t, c):
        pass


# Global cognition hub (shared)
WM = WorldModel()


def _safe_tools(ts: List[str]) -> List[str]:
    return [t for t in ts if allow_tool(t)]


def run_autonomous_loop(user_id: str = "default_user", tick_seconds: float = 1.5):
    os.makedirs("logs", exist_ok=True)
    identity = load_identity(user_id)
    log_trace(user_id, "BOOT", f"Autopilot for {identity.get('name')}")

    # Simple bandit for choosing “strategy” tool first
    bandit = EpsilonGreedyBandit(
        ["react_plan", "direct_execute", "reflect_first"], epsilon=0.15
    )
    convo_hist: List[str] = []

    while True:
        # === 1) Generate intrinsic goal
        goal = generate_intrinsic_goal(user_id)
        log_trace(user_id, "GOAL", goal)

        # === 2) Hierarchical planning + safety
        subplan = plan_with_checks(goal)
        subplan = [s for s in subplan if check_text_action(s)]
        log_trace(user_id, "PLAN", "\n".join(subplan))

        # === 3) Strategy selection by bandit
        strategy = bandit.select()
        log_trace(user_id, "STRATEGY", strategy)

        result_chunks = []
        for step in subplan:
            # optional ReAct chain when strategy requires
            tools = (
                _safe_tools(react_tool_chain(step))
                if strategy in ("react_plan",)
                else []
            )

            # pre-check (approval for risky text)
            if not approve(step):
                fix = critique(step)
                step = f"{step}\n[Auto-Fix]\n{fix}"
                log_trace(user_id, "STEP_FIX", fix)

            # tool-first if available
            if tools:
                for t in tools:
                    if not check_text_action(f"tool:{t}"):
                        result_chunks.append(f"[BLOCKED] {t}")
                        continue
                    out = execute_tool(t, step, user_id)
                    result_chunks.append(f"[{t}] {str(out)[:400]}")
            else:
                # fallback: just attempt via LLM execution reasoning if needed
                from javu_agi.llm import call_llm

                out = call_llm(
                    f"Eksekusi langkah ini secara konseptual dan berikan hasil ringkas:\n{step}",
                    task_type="reason",
                    user_id=user_id,
                    max_tokens=512,
                )
                result_chunks.append(out)

            # detect failure → replan this step
            if detect_plan_failure(result_chunks[-1]):
                alt_steps = generate_alternative_plan(step)
                result_chunks.append(
                    "→ Replan:\n" + "\n".join(f"- {s}" for s in alt_steps)
                )

        result = "\n".join(result_chunks)

        # === 4) Reflect & reward
        convo_hist.extend([f"[GOAL] {goal}", f"[RESULT]\n{result}"])
        try:
            reflection = reflect_on_conversation(user_id, convo_hist[-10:])
        except Exception:
            reflection = "Reflection minimal."
        reward = compute_reward(reflection, goal, result)
        log_trace(user_id, "REFLECTION", reflection)
        log_trace(user_id, "REWARD", reward)

        # Bandit update (success proxy)
        bandit.update(strategy, float(reward))

        # === 5) World model update
        WM.update_world_state(
            {"goal": goal, "result": result, "reflection": reflection},
            source="autopilot",
        )

        # === 6) Learn & consolidate
        ingest_experience(user_id, reflection)
        consolidate_knowledge(user_id)
        update_policy_from_reflection(user_id)

        # === 7) Sleep between cycles
        time.sleep(tick_seconds)
