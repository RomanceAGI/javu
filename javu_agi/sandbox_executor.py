from javu_agi.simulated_env import simulate_tool_execution, evaluate_plan_in_sim
from javu_agi.tool_executor import execute_tool


def run_in_sandbox(plan_steps: list[str]) -> dict:
    sim_result = evaluate_plan_in_sim(plan_steps)
    return sim_result


def safe_execute_if_valid(plan_steps: list[str]) -> str:
    sim = run_in_sandbox(plan_steps)
    if all("sukses" in r.lower() for r in sim.values()):
        final_result = []
        for step in plan_steps:
            result = execute_tool(step)
            final_result.append(f"[STEP] {step} → {result}")
        return "\n".join(final_result)
    else:
        return "[SANDBOX BLOCKED] Plan contains unsafe or failed step(s)"
