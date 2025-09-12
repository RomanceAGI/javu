from __future__ import annotations
from typing import List, Dict
import re
from javu_agi.memory.memory_procedural import ProceduralMemory


class SkillComposer:
    """
    Komposisi multi-skill -> langkah plan.
    - Ambil N skill paling cocok (keyword overlap) dan urutkan: pre -> core -> post
    - Inject parameter sederhana {{query}} ke template
    """

    def __init__(self, max_skills: int = 3):
        self.proc = ProceduralMemory()
        self.max_skills = max_skills

    def _score(self, template: str, query: str) -> int:
        toks = set(re.findall(r"[a-zA-Z0-9_\-]+", query.lower()))
        kws = set(re.findall(r"[a-zA-Z0-9_\-]+", template.lower()))
        return len(toks & kws)

    def compose(self, query: str) -> List[Dict]:
        sks = self.proc.recall_skill("generic")
        ranked = sorted(
            sks,
            key=lambda s: self._score(s.parameters.get("template", ""), query),
            reverse=True,
        )
        steps: List[Dict] = []
        for sk in ranked[: self.max_skills]:
            templ = sk.parameters.get("template", "")
            templ = templ.replace("{{query}}", query)  # param sederhana
            cmd = (
                "python - <<'PY'\n"
                "text = '''" + templ.replace("'''", "'")[:2000] + "'''\n"
                "print(text)\nPY"
            )
            steps.append({"tool": "python", "cmd": cmd, "skill_id": sk.skill_id})
        return steps
