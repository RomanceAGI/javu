from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Any
import random


@dataclass
class Bucket:
    name: str
    items: List[Dict[str, Any]] = field(default_factory=list)
    win_rate: float = 0.5


class Curriculum:
    def __init__(self):
        self.buckets: List[Bucket] = [
            Bucket("general"),
            Bucket("coding"),
            Bucket("reasoning"),
            Bucket("research"),
        ]
        self.stage = 0  # 0=easy → n=hard

    def record_result(self, bucket: str, win: bool):
        for b in self.buckets:
            if b.name == bucket:
                # EMA win-rate
                alpha = 0.2
                b.win_rate = (1 - alpha) * b.win_rate + alpha * (1.0 if win else 0.0)

    def harder(self):
        self.stage = min(self.stage + 1, 5)

    def easier(self):
        self.stage = max(self.stage - 1, 0)


class Sampler:
    def __init__(self, cur: Curriculum, stage: int = 0, batch: int = 8):
        self.cur = cur
        self.stage = stage
        self.batch = batch

    def next_batch(self) -> List[Dict[str, Any]]:
        # sampling cond. pada stage: makin tinggi → lebih banyak dari bucket ber-win_rate tinggi
        weights = [max(0.1, b.win_rate + 0.05 * self.stage) for b in self.cur.buckets]
        total = sum(weights)
        probs = [w / total for w in weights]
        out: List[Dict[str, Any]] = []
        for _ in range(self.batch):
            b = random.choices(self.cur.buckets, weights=probs, k=1)[0]
            if not b.items:
                out.append(
                    {
                        "prompt": "Ringkas artikel umum.",
                        "rule": "coherent",
                        "tags": [b.name],
                    }
                )
            else:
                out.append(random.choice(b.items))
        return out


# --- ADD: loader dari bank dict (tag -> list of items) ---
def load_bank(cur: Curriculum, bank: Dict[str, List[Dict[str, Any]]]):
    name2b = {b.name: b for b in cur.buckets}
    for tag, items in (bank or {}).items():
        b = name2b.get(tag)
        if not b:
            b = Bucket(tag)
            cur.buckets.append(b)
        # normalisasi item: wajib ada "id", "prompt"
        norm = []
        for it in items:
            iid = it.get("id") or f"{tag}:{hash(it.get('prompt','')) & 0xffffffff:x}"
            norm.append(
                {
                    "id": iid,
                    "prompt": it.get("prompt", ""),
                    "rule": it.get("rule", "coherent"),
                    "tags": it.get("tags", [tag]),
                    "meta": it.get("meta", {}),
                }
            )
        b.items = norm


# --- ADD: update granular per case + adapt stage ---
def update_result(cur: Curriculum, tag: str, case_id: str, ok: bool, sec: float):
    # EMA win-rate per bucket
    cur.record_result(tag, ok)
    # simple pacing: gagal → turunin stage, sukses cepat → naikin
    if ok and sec < 1.0:
        cur.harder()
    elif not ok:
        cur.easier()


def build_default_curriculum() -> Curriculum:
    return Curriculum()
