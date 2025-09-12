from __future__ import annotations
import os, json, uuid, time
from typing import Dict, Any
from javu_agi.memory.memory_procedural import ProceduralMemory
from javu_agi.memory.memory_schemas import Skill

TRACE_DIR = "trace/logs"


class SkillDaemon:
    """
    Pantau trace episodik; kalau pola draft + label SELECT stabil,
    ekstrak jadi 'Skill' dengan template.
    """

    def __init__(self, interval_s: int = 10):
        self.proc = ProceduralMemory()
        self.interval_s = interval_s
        self._seen = set()

    def _scan_episode(self, user: str, ep: str):
        path = f"{TRACE_DIR}/{user}/{ep}/graph.jsonl"
        if not os.path.exists(path):
            return
        with open(path, "r", encoding="utf-8") as f:
            lines = [json.loads(x) for x in f if x.strip()]
        drafts = [
            x for x in lines if x.get("t") == "NODE" and x.get("kind") == "THOUGHT"
        ]
        selects = [
            x for x in lines if x.get("t") == "NODE" and x.get("kind") == "SELECT"
        ]
        if not drafts or not selects:
            return
        # template sederhana: ambil draft terbaik & jadikan template skill
        best = selects[-1]["content"]["choice"]["text"]
        if len(best) < 40:
            return  # hindari template sampah
        sk = Skill(
            skill_id=str(uuid.uuid4()),
            name="generic",
            parameters={
                "template": best[:600],
                "keywords": list(set(best.lower().split()[:8])),
            },
            preconditions=[],
            postconditions=[],
        )
        self.proc.store_skill(sk)

    def run_forever(self, *a, **k):
        raise RuntimeError("skill daemon disabled: builder OFF")


if __name__ == "__main__":
    SkillDaemon(10).run_forever()
