import os, time, shutil
from pathlib import Path


def _rm(path: Path):
    try:
        if path.is_dir():
            shutil.rmtree(path, ignore_errors=True)
        else:
            path.unlink(missing_ok=True)
    except Exception:
        pass


def _purge_dir(root: str, older_than_days: int, patterns=("*",)):
    if older_than_days <= 0:
        return
    now = time.time()
    cutoff = older_than_days * 86400
    p = Path(root)
    if not p.exists():
        return
    for pat in patterns:
        for f in p.rglob(pat):
            try:
                if not f.exists():
                    continue
                age = now - f.stat().st_mtime
                if age >= cutoff:
                    _rm(f)
            except Exception:
                continue


def sweep():
    keep_art = int(os.getenv("RETAIN_DAYS_ARTIFACTS", "14"))
    keep_met = int(os.getenv("RETAIN_DAYS_METRICS", "30"))
    _purge_dir(os.getenv("ARTIFACTS_DIR", "/artifacts"), keep_art)
    _purge_dir(os.getenv("METRICS_DIR", "/data/metrics"), keep_met)
