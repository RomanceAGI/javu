from __future__ import annotations
import json, pathlib, time
from typing import Dict, Any

VAL_FILE = pathlib.Path("trace/value_alignment.jsonl")


class ValueAlignmentTrainer:
    def __init__(self, value_memory):
        self.vm = value_memory

    def update_from_feedback(
        self, record: Dict[str, Any], feedback: Dict[str, Any]
    ) -> Dict[str, Any]:
        score = int(feedback.get("human", 0))
        rationale = feedback.get("explanation", "")
        payload = {
            "ts": time.time(),
            "intent_id": record.get("intent_id"),
            "verdict": record.get("verdict"),
            "score": score,
            "rationale": rationale,
        }
        # update value memory with structured feedback
        self.vm.update(record, {"human_feedback": score, "reason": rationale})
        VAL_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(VAL_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(payload, ensure_ascii=False) + "\n")
        # optional: adapt global preference weights (simple EMA)
        self._adapt_global_weights(score)
        return {"status": "ok", "applied": True, "delta": score}

    def _adapt_global_weights(self, score: int, alpha: float = 0.05):
        # hook: increase emphasis on human wellbeing when negative feedback occurs
        try:
            current = pathlib.Path("trace/value_weights.json")
            w = {"human": 1.0, "nature": 1.0, "innovation": 1.0}
            if current.exists():
                w.update(json.loads(current.read_text()))
            if score < 0:
                w["human"] = min(2.0, w["human"] + alpha)
                w["nature"] = min(2.0, w["nature"] + alpha / 2)
            else:
                w["innovation"] = min(2.0, w["innovation"] + alpha / 3)
            current.write_text(json.dumps(w))
        except Exception:
            pass
