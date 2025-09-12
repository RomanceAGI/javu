import os, json, time
from typing import Any, Dict, List
from javu_agi.telemetry.signing import sign_line


def _ensure_dir(p: str) -> None:
    os.makedirs(os.path.dirname(p), exist_ok=True)


def journal_path(metrics_dir: str, episode_id: str) -> str:
    p = os.path.join(metrics_dir or "/data/metrics", "journal", f"{episode_id}.jsonl")
    _ensure_dir(p)
    return p


def write_journal(path: str, record: Dict[str, Any]) -> None:
    try:
        _ensure_dir(path)
        rec = dict(record or {})
        if "ts" not in rec:
            rec["ts"] = int(time.time() * 1000)
        with open(path, "a", encoding="utf-8") as f:
            s = json.dumps(rec, ensure_ascii=False)
            f.write(sign_line(s) + "\n")
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception:
        pass  # jangan ganggu eksekusi


def load_journal(path: str) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    try:
        if not os.path.isfile(path):
            return out
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    out.append(json.loads(line))
                except Exception:
                    continue
    except Exception:
        return out
    return out
