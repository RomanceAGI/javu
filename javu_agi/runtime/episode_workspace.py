import os, time
from pathlib import Path


def make_workspace(base: str, ep_id: str) -> str:
    p = Path(base) / f"ep_{ep_id}_{int(time.time())}"
    p.mkdir(parents=True, exist_ok=True)
    return str(p)
