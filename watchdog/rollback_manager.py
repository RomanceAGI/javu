from __future__ import annotations
from pathlib import Path
from datetime import datetime
import shutil, os, json

BACKUP_DIR = Path("backups")
BACKUP_DIR.mkdir(exist_ok=True)

def _stamp() -> str:
    return datetime.utcnow().strftime("%Y%m%d-%H%M%S")

def create_backup(files):
    ts = _stamp()
    dst = BACKUP_DIR / ts
    dst.mkdir(exist_ok=True)
    for f in files:
        p = Path(f)
        if p.exists():
            shutil.copy2(p, dst / p.name)

def _latest_backup_of(filename: str) -> Path | None:
    cands = sorted(BACKUP_DIR.glob("*/" + Path(filename).name), reverse=True)
    return cands[0] if cands else None

def rollback(filename: str):
    src = _latest_backup_of(filename)
    if not src: return
    shutil.copy2(src, filename)
