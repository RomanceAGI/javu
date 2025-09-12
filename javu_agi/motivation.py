from typing import List
from javu_agi.llm import call_llm

INNATE_DRIVES = ["curiosity", "mastery", "helpfulness", "truth"]


def propose_goals_from_drives(context: str, top_k: int = 3) -> List[str]:
    prompt = f"""
Konteks:\n{context}\n
Dengan mengacu pada drives {", ".join(INNATE_DRIVES)}, usulkan {top_k} goal bernilai tinggi,
spesifik, aman, dan bisa dieksekusi. Jawab berupa daftar (satu per baris).
"""
    out = call_llm(prompt, task_type="plan", temperature=0.2, max_tokens=256)
    return [x.strip("- ").strip() for x in out.splitlines() if x.strip()][:top_k]
