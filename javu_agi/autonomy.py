from __future__ import annotations
import os, time, json, random, glob
from typing import Dict, Any, Optional

from javu_agi.safety_values import classify


class AutonomyGate:
    """Flag-file gate + throttle sederhana agar otonomi aman dikontrol."""

    def __init__(self, base_dir="/data/run"):
        self.dir = base_dir
        os.makedirs(self.dir, exist_ok=True)
        self.flag = os.path.join(self.dir, "autonomy.enabled")

    def enable(self):
        open(self.flag, "w").close()

    def disable(self):
        try:
            os.remove(self.flag)
        except FileNotFoundError:
            pass

    def is_on(self) -> bool:
        return os.path.exists(self.flag)


def _load_bank_jsonl(path: str, limit: int = 200):
    out = []
    try:
        with open(path, "r", encoding="utf-8") as f:
            for i, line in enumerate(f):
                if i >= limit:
                    break
                try:
                    obj = json.loads(line)
                    p = (obj.get("prompt") or "").strip()
                    if p:
                        out.append(
                            {
                                "id": obj.get("id") or f"bank-{i}",
                                "prompt": p,
                                "priority": 0.5,
                            }
                        )
                except Exception:
                    continue
    except Exception:
        pass
    return out


def _load_recent_traces(
    dir_glob: str = "/data/artifacts/episodes/**/*.json", limit: int = 50
):
    out = []
    try:
        files = sorted(glob.glob(dir_glob, recursive=True))[-limit:]
        for fp in files:
            try:
                with open(fp, "r", encoding="utf-8") as f:
                    obj = json.load(f)
                    p = (obj.get("prompt") or obj.get("task") or "").strip()
                    if p:
                        out.append(
                            {
                                "id": f"trace:{os.path.basename(fp)}",
                                "prompt": p,
                                "priority": 0.3,
                            }
                        )
            except Exception:
                continue
    except Exception:
        pass
    return out


def pick_goal(goals, drive, memory) -> Optional[Dict[str, Any]]:
    cand = []
    # 1) goal aktif dari GoalManager
    try:
        cand += list(goals.list_active() or [])
    except Exception:
        pass
    # 2) auto bank aman (sudah di-guard/fuzz)
    bank = os.getenv("AUTO_BANK", "/data/task_bank/auto_hard.safe.jsonl")
    if os.path.exists(bank):
        cand += _load_bank_jsonl(bank, limit=200)
    # 3) recent traces (reinforce)
    cand += _load_recent_traces(limit=50)

    if not cand:
        # fallback kecil berbasis memory
        mem = getattr(memory, "sample_recent", lambda n=3: [])(3) or []
        if not mem:
            return None
        prompt = f"Susun ringkasan harian artefak: {[m.get('key','') for m in mem]}"
        return {"id": f"auto-{int(time.time())}", "prompt": prompt, "priority": 0.4}

    scored = []
    for g in cand:
        desc = (g.get("desc") or g.get("prompt") or g.get("name") or "").strip()
        if not desc:
            continue
        pid = g.get("id") or g.get("name") or str(time.time())
        impact = float(getattr(drive, "estimate_impact_gap", lambda _: 0.5)(desc))
        novelty = float(getattr(memory, "novelty", lambda _: 0.5)(desc))
        rec = float(g.get("recency", 1.0))
        pri = float(g.get("priority", 0.5))
        score = pri * impact * (0.6 + 0.4 * novelty) * rec
        scored.append((score, {**g, "id": pid, "prompt": desc}))
    scored.sort(key=lambda x: x[0], reverse=True)
    return scored[0][1] if scored else None
