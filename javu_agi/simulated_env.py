def simulate_tool_execution(tool_instruction: str) -> str:
    return f"[SIMULATION] '{tool_instruction}' dieksekusi secara virtual."


def evaluate_plan_in_sim(plan_steps: list[str]) -> dict:
    return {
        step: ("Simulasi sukses" if "delete" not in step.lower() else "Simulasi gagal")
        for step in plan_steps
    }
