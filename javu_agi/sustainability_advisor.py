from __future__ import annotations
import re


def suggest(task: str) -> str:
    t = task.lower()
    if re.search(
        r"(gpu|mining|render farm|brute[- ]force|train model|fine[- ]tune)", t
    ):
        return "Prefer efficient retrieval, pruning search space, or approximate methods; avoid heavy compute."
    if re.search(r"(travel|delivery|logistics)", t):
        return "Batch tasks, choose nearest providers, prefer low-emission options."
    return ""
