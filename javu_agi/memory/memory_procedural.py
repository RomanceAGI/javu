from .schemas import Skill
import json
from pathlib import Path
from datetime import datetime
from typing import List

SKILL_FILE = Path("data/memory/skills.json")
SKILL_FILE.parent.mkdir(parents=True, exist_ok=True)


class ProceduralMemory:
    def __init__(self):
        if not SKILL_FILE.exists():
            json.dump([], open(SKILL_FILE, "w"))

    def store_skill(self, skill: Skill):
        skills = json.load(open(SKILL_FILE))
        skills.append(skill.dict())
        json.dump(skills, open(SKILL_FILE, "w"), ensure_ascii=False, indent=2)

    def recall_skill(self, name: str) -> List[Skill]:
        skills = json.load(open(SKILL_FILE))
        return [Skill(**s) for s in skills if s["name"] == name]

    def increment_usage(self, skill_id: str):
        skills = json.load(open(SKILL_FILE))
        for s in skills:
            if s["skill_id"] == skill_id:
                s["usage_count"] += 1
                s["last_used"] = datetime.utcnow().isoformat()
        json.dump(skills, open(SKILL_FILE, "w"), ensure_ascii=False, indent=2)
