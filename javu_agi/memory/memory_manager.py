from __future__ import annotations
from typing import List, Dict, Any
import time

from javu_agi.memory.episodic_memory import EpisodicMemory
from javu_agi.memory.memory_semantic import SemanticMemory
from javu_agi.memory.memory_procedural import ProceduralMemory
from javu_agi.memory.memory_schemas import Episode, SemanticFact, Skill
from javu_agi.memory.consolidation import Consolidator, MemItem


class MemoryManager:
    def __init__(self):
        self.episodic = EpisodicMemory()
        self.semantic = SemanticMemory()
        self.procedural = ProceduralMemory()

    # ---- store ----
    def store_episode(self, episode: Episode):
        self.episodic.store(episode)

    def store_fact(self, fact: SemanticFact):
        self.semantic.store(fact)

    def store_skill(self, skill: Skill):
        self.procedural.store_skill(skill)

    # ---- recall ----
    def recall_context(self, query: str) -> Dict[str, Any]:
        sem = self.semantic.search(query)
        epi = self.episodic.recall_recent(limit=3)
        return {"semantic": sem, "episodic": epi}

    # ---- consolidate (FIX: self.store → gunakan komponen yang ada) ----
    def consolidate(self) -> dict:
        """
        Sample episodic+semantic → rencanakan keep/merge/drop → terapkan.
        Return ringkasan langkah yang diambil.
        """
        now = int(time.time())
        items: List[MemItem] = []

        # ambil subset aman dari masing-masing store (fallback kalau API tidak ada)
        try:
            epis = self.episodic.list(limit=500)  # prefer .list()
        except AttributeError:
            epis = self.episodic.recall_recent(limit=500)
        try:
            sems = self.semantic.list(limit=500)
        except AttributeError:
            sems = self.semantic.search("")[:500]

        for e in epis:
            items.append(
                MemItem(
                    kind="episodic",
                    text=getattr(e, "prompt", None) or getattr(e, "summary", "") or "",
                    meta={
                        "ts": int(getattr(e, "timestamp", now)),
                        "reward": float(getattr(e, "reward", 0.0)),
                        "used": int(getattr(e, "used", 0)),
                        "novelty": 0.0,
                    },
                )
            )
        for s in sems:
            items.append(
                MemItem(
                    kind="semantic",
                    text=getattr(s, "content", "") or "",
                    meta={
                        "ts": int(getattr(s, "timestamp", now)),
                        "reward": float(getattr(s, "reward", 0.0)),
                        "used": int(getattr(s, "used", 0)),
                        "novelty": float(getattr(s, "novelty", 0.0)),
                    },
                )
            )

        C = Consolidator(now=now)
        plan = C.plan(items)

        # apply merges
        for win, lose in plan["merge"]:
            a = items[win]
            b = items[lose]
            merged = C.merge_text(a.text, b.text)
            if a.kind == "semantic":
                try:
                    self.semantic.update_text(old=a.text, new=merged)
                except AttributeError:
                    pass
            if b.kind == "semantic":
                try:
                    self.semantic.delete_text(b.text)
                except AttributeError:
                    pass

        # apply drops by TTL
        for idx in plan["drop"]:
            m = items[idx]
            try:
                if m.kind == "episodic":
                    self.episodic.delete_text(m.text)
                else:
                    self.semantic.delete_text(m.text)
            except AttributeError:
                # abaikan jika backend belum sediakan API delete_text
                pass

        return {
            "kept": len(plan["keep"]),
            "merged": len(plan["merge"]),
            "dropped": len(plan["drop"]),
        }
