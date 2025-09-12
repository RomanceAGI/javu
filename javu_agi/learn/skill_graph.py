from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Any, Tuple
import hashlib, json, os, time


def _hash(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8", "ignore")).hexdigest()[:16]


@dataclass
class SkillNode:
    tool: str
    cmd: str
    id: str = field(default_factory=lambda: _hash(str(time.time())))


class SkillGraph:
    """
    Komposisi langkah (linear/DAG kecil) + cache hasil eksekusi.
    Cache level: per-cmd hash -> output (stdout).
    """

    def __init__(self, cache_dir: str = "data/skill_cache"):
        self.cache_dir = cache_dir
        os.makedirs(self.cache_dir, exist_ok=True)

    def _key(self, cmd: str, tool: str = "") -> str:
        return _hash(f"{tool}::{cmd}")

    def cache_get(self, cmd: str, tool: str = "") -> str | None:
        k = os.path.join(self.cache_dir, self._key(cmd, tool) + ".json")
        if not os.path.exists(k):
            return None
        try:
            o = json.load(open(k, "r", encoding="utf-8"))
            return o.get("stdout", "")
        except Exception:
            return None

    def cache_put(self, cmd: str, stdout: str, tool: str = ""):
        k = os.path.join(self.cache_dir, self._key(cmd, tool) + ".json")
        try:
            json.dump({"stdout": stdout[:32000]}, open(k, "w", encoding="utf-8"))
        except Exception:
            pass

    def expand_and_cache(self, steps: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        out = []
        for s in steps:
            tool = s.get("tool", "python")
            cmd = s.get("cmd", "")
            if not cmd:
                continue
            tag = self._key(cmd, tool)
            cmd_tagged = cmd + f"  # cache:{tag}"
            out.append({"tool": tool, "cmd": cmd_tagged})
        return out

    def reuse_ratio(self) -> float:
        try:
            files = [f for f in os.listdir(self.cache_dir) if f.endswith(".json")]
            if not files:
                return 0.0
            import time

            now = time.time()
            used = sum(
                1
                for f in files
                if now - os.path.getmtime(os.path.join(self.cache_dir, f)) < 7 * 86400
            )
            return round(used / max(1, len(files)), 3)
        except Exception:
            return 0.0
