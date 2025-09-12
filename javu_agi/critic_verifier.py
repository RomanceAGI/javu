from javu_agi.llm import call_llm


def critique(plan_or_step: str) -> str:
    prompt = f"Critique singkat rencana/step berikut. Cari risiko, asumsi salah, dan saran perbaikan:\n{plan_or_step}"
    return call_llm(prompt, task_type="reflect", temperature=0.3, max_tokens=256)


def approve(plan_or_step: str) -> bool:
    ans = call_llm(
        f"Apakah step ini aman dan layak dieksekusi? Jawab 'YES' atau 'NO'.\n{plan_or_step}",
        task_type="reflect",
        temperature=0.0,
        max_tokens=8,
    )
    return "YES" in ans.upper()
