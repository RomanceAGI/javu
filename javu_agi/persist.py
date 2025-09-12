import os, json, time
from pathlib import Path


def _p(dir, name):
    Path(dir).mkdir(parents=True, exist_ok=True)
    return str(Path(dir) / name)


class CheckpointIO:
    def __init__(self, base=os.getenv("ARTIFACTS_DIR", "/artifacts")):
        self.dir = str(Path(base) / "ckpt")
        Path(self.dir).mkdir(parents=True, exist_ok=True)

    def save(self, name: str, obj) -> str:
        # pakai state_dict kalau ada; kalau enggak, __dict__ minimum
        if hasattr(obj, "state_dict"):
            state = obj.state_dict()
        else:
            state = getattr(obj, "__dict__", {})
        path = _p(self.dir, f"{name}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"ts": int(time.time()), "state": state}, f, ensure_ascii=False)
        return path

    def load(self, name: str, obj) -> bool:
        path = _p(self.dir, f"{name}.json")
        if not os.path.isfile(path):
            return False
        try:
            J = json.load(open(path, "r", encoding="utf-8"))
            state = J.get("state", {})
            if hasattr(obj, "load_state_dict"):
                obj.load_state_dict(state)
            else:
                for k, v in state.items():
                    setattr(obj, k, v)
            return True
        except Exception:
            return False
