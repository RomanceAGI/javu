from __future__ import annotations
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
import math, time


@dataclass
class MemItem:
    kind: str
    text: str
    meta: Dict[str, Any]


class Consolidator:
    """
    - Score tiap item: f(recency, reward, usage, novelty)
    - Merge semantic duplikat → ringkas
    - Forgetting terkontrol: TTL dinamis berbasis skor
    - Output: {keep, merge, drop}
    """

    def __init__(self, now: Optional[int] = None):
        self.now = int(now or time.time())

    def _score(self, m: MemItem) -> float:
        ts = int(m.meta.get("ts", self.now))
        age = max(1, self.now - ts)  # detik
        days = age / 86400.0
        rec = math.exp(-0.25 * days)  # recency [0..1]
        rew = float(m.meta.get("reward", 0.0))  # [-1..1] expected
        use = float(m.meta.get("used", 0))  # freq recall
        nov = float(m.meta.get("novelty", 0.0))  # [0..1]
        base = (
            0.4 * rec + 0.35 * max(0.0, rew) + 0.2 * math.tanh(use / 5.0) + 0.05 * nov
        )
        return round(max(0.0, min(1.0, base)), 4)

    def _ttl_days(self, score: float, kind: str) -> int:
        # TTL dinamis: high-score keep longer
        base = 3 if kind == "episodic" else 14
        if score >= 0.8:
            return 180
        if score >= 0.6:
            return 60
        if score >= 0.4:
            return 21
        return base

    def plan(self, items: List[MemItem]) -> Dict[str, Any]:
        # 1) skoring
        scored = [{"item": m, "score": self._score(m)} for m in items]
        # 2) cluster semantic duplikat sederhana (hash by lower 80 chars)
        buckets: Dict[str, List[int]] = {}
        for i, s in enumerate(scored):
            key = (s["item"].kind, (s["item"].text.strip().lower()[:80]))
            buckets.setdefault(str(key), []).append(i)

        merges = []
        drops = []
        keeps = []
        for key, idxs in buckets.items():
            # sort by score desc
            idxs.sort(key=lambda i: scored[i]["score"], reverse=True)
            # kandidat utama
            head = idxs[0]
            keeps.append(head)
            # sisanya jika sangat mirip → merge
            for j in idxs[1:]:
                t1 = scored[head]["item"].text.strip().lower()
                t2 = scored[j]["item"].text.strip().lower()
                # mirip kalau Jaccard token > 0.7
                A = set(t1.split())
                B = set(t2.split())
                jac = len(A & B) / max(1, len(A | B))
                if jac >= 0.7:
                    merges.append((head, j))
                else:
                    # low-score → drop jika TTL habis
                    days = self._ttl_days(scored[j]["score"], scored[j]["item"].kind)
                    age_days = (
                        self.now - int(scored[j]["item"].meta.get("ts", self.now))
                    ) / 86400.0
                    if age_days > days and scored[j]["score"] < 0.4:
                        drops.append(j)
                    else:
                        keeps.append(j)

        # unique-ify
        keeps = sorted(list(set(keeps)))
        drops = sorted(list(set(drops)) - set(keeps))
        # TTL rekomendasi per item
        ttl_map = {
            i: self._ttl_days(scored[i]["score"], scored[i]["item"].kind) for i in keeps
        }
        return {
            "scored": scored,
            "keep": keeps,
            "merge": merges,  # (winner_index, drop_index)
            "drop": drops,
            "ttl_days": ttl_map,
        }

    def merge_text(self, a: str, b: str, max_len: int = 600) -> str:
        # ringkas naive: ambil kalimat unik awal dari a + b hingga max_len
        seen = set()
        out = []
        for s in (a + " " + b).split("."):
            t = s.strip()
            if not t:
                continue
            key = t.lower()[:60]
            if key in seen:
                continue
            seen.add(key)
            out.append(t)
            if sum(len(x) for x in out) > max_len:
                break
        return ". ".join(out) + "."
