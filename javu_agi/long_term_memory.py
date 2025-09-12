import os, json, time
from typing import List, Dict, Any


class LongTermMemory:
    def __init__(self, base_dir: str):
        self.dir = os.path.join(base_dir, "ltm")
        os.makedirs(self.dir, exist_ok=True)
        self.path = os.path.join(self.dir, "events.jsonl")

    def store_event(self, kind: str, data: Dict[str, Any]):
        """Append an event to the JSONL log.

        Any file I/O error is intentionally ignored to avoid taking down the system
        when the underlying storage is unavailable. We catch Exception explicitly
        to avoid suppressing system-exiting exceptions like KeyboardInterrupt.
        """
        try:
            event = {"ts": int(time.time() * 1000), "kind": kind, **(data or {})}
            with open(self.path, "a", encoding="utf-8") as f:
                f.write(json.dumps(event, ensure_ascii=False) + "\n")
        except Exception:
            # Intentionally ignore file I/O errors; upstream components can decide
            # whether to alert on missing events.
            return

    def recent(self, n: int = 50) -> List[Dict[str, Any]]:
        """Return the most recent ``n`` events from the log.

        Any issues reading the file (e.g. missing file) result in an empty list.
        Invalid JSON lines are skipped rather than raising an exception.
        """
        out: List[Dict[str, Any]] = []
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        out.append(json.loads(line))
                    except json.JSONDecodeError:
                        # Skip malformed lines
                        continue
            # Only keep the last n events
            out = out[-n:]
        except Exception:
            # On I/O errors return an empty list
            return []
        return out

    def summarize_recent(self, n: int = 100) -> Dict[str, Any]:
        """Summarise recent events.

        Returns a dict with counts of events, a frequency table of kinds, and a simple
        knowledge graph (subject → [(relation, object)]). The second return in the
        original implementation was unreachable; the consolidated structure below
        preserves the most informative version.
        """
        ev = self.recent(n)
        kg: Dict[str, set] = {}
        for e in ev:
            s = e.get("subject")
            r = e.get("relation")
            o = e.get("object")
            if s and r and o:
                kg.setdefault(s, set()).add((r, o))
        return {
            "count": len(ev),
            "kinds": {e["kind"]: 1 for e in ev if "kind" in e},
            "kg": {k: list(v) for k, v in kg.items()},
        }
