import time, json, os
from typing import Dict, Any


class FeedbackCollector:
    def __init__(self, path="./logs/feedback.jsonl") -> None:
        self.path = path
        os.makedirs(os.path.dirname(self.path), exist_ok=True)

    def record(
        self, user_id: str, response: Dict[str, Any], score: int, note: str = ""
    ) -> None:
        rec = {
            "ts": int(time.time()),
            "user": user_id,
            "score": score,
            "note": note,
            "resp": response,
        }
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    _ewma = {}

    def update_ewma(key: str, score: float, alpha: float = 0.3):
        avg, a = _ewma.get(key, (score, alpha))
        avg = a * score + (1 - a) * avg
        _ewma[key] = (avg, a)
        return avg
