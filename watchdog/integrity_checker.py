from __future__ import annotations
import hashlib, json
from pathlib import Path
from typing import Dict

try:
    from trace.trace_logger import log_node
except Exception:
    from trace.trace_logger import log_node

try:
    from watchdog.rollback_manager import rollback, create_backup
except Exception:
    from watchdog.rollback_manager import rollback, create_backup

CRITICAL_FILES = [Path("core_loop.py"), Path("javu_agi/world_model.py"), Path("javu_agi/executive_controller.py")]

def _sha256(path: Path) -> str:
    if not path.exists(): return "MISSING"
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def snapshot_reference() -> Dict[str, str]:
    ref = {str(p): _sha256(p) for p in CRITICAL_FILES}
    Path("logs").mkdir(exist_ok=True)
    Path("logs/integrity_reference.json").write_text(json.dumps(ref, indent=2))
    create_backup([str(p) for p in CRITICAL_FILES])
    return ref

def check_integrity(autorollback: bool = True) -> Dict[str, str]:
    ref_path = Path("logs/integrity_reference.json")
    if not ref_path.exists(): return snapshot_reference()
    ref = json.loads(ref_path.read_text())
    cur = {str(p): _sha256(p) for p in CRITICAL_FILES}
    for f, rh in ref.items():
        ch = cur.get(f, "MISSING")
        if ch != rh and autorollback:
            rollback(f)
    return cur
