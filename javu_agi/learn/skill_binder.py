from __future__ import annotations
from typing import List, Dict
import re
from javu_agi.memory.memory_procedural import ProceduralMemory


class SkillBinder:
    """
    Ambil skill dari ProceduralMemory → cocokkan ke prompt → hasilkan langkah tool siap eksekusi.
    Tujuan: pakai 'kebiasaan sukses' masa lalu sebagai aksi cepat.
    """

    def __init__(self, max_skills: int = 2):
        self.proc = ProceduralMemory()
        self.max_skills = max_skills

    def _tokenize(self, s: str) -> List[str]:
        return re.findall(r"[a-zA-Z0-9_\-]+", s.lower())

    def bind(self, prompt: str) -> List[Dict]:
        toks = set(self._tokenize(prompt))
        # sementara ambil semua skill "generic"
        sks = self.proc.recall_skill("generic")
        # ranking sederhana: banyaknya overlap keyword
        ranked = []
        for sk in sks:
            kws = set([k for k in sk.parameters.get("keywords", [])])
            score = len(kws & toks)
            if score > 0:
                ranked.append((score, sk))
        ranked.sort(key=lambda t: t[0], reverse=True)
        steps: List[Dict] = []
        for _, sk in ranked[: self.max_skills]:
            template = sk.parameters.get("template", "")
            # ubah template jadi langkah python sederhana (bisa diganti tool lain)
            cmd = (
                "python - <<'PY'\n"
                "text = '''" + template.replace("'''", "'")[:1000] + "'''\n"
                "print(text)\nPY"
            )
            steps.append({"tool": "python", "cmd": cmd, "skill_id": sk.skill_id})
        return steps
