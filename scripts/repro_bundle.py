from __future__ import annotations
import os, json, shutil, tempfile, time, glob
from pathlib import Path
from typing import Optional

def make_bundle(trace_id: Optional[str], outdir: str = "artifacts/repro") -> str:
    os.makedirs(outdir, exist_ok=True)
    ts = time.strftime("%Y%m%d-%H%M%S")
    base = Path(tempfile.mkdtemp(prefix="repro_"))
    # collect
    def _copy(pattern: str, dst_name: str):
        dst = base / dst_name
        dst.mkdir(parents=True, exist_ok=True)
        for fp in glob.glob(pattern):
            try: shutil.copy(fp, dst)
            except Exception: pass

    _copy(os.getenv("ROUTER_TRACE", "logs/router_trace*.jsonl"), "router")
    _copy(os.path.join(os.getenv("AUDIT_DIR","artifacts/audit_chain"), "*.jsonl"), "audit")
    _copy(os.getenv("TRANSPARENCY_LOG","artifacts/transparency.jsonl"), "transparency")
    _copy(os.path.join(os.getenv("METRICS_DIR","/data/metrics"), "*.prom"), "metrics")
    # filter by trace_id if provided
    if trace_id:
        # naive filter
        for f in (base/"router").glob("*.jsonl"):
            with open(f,"r+",encoding="utf-8") as fh:
                lines = [ln for ln in fh if trace_id in ln]
            with open(f,"w",encoding="utf-8") as fh:
                fh.writelines(lines)
    # zip
    zip_path = os.path.join(outdir, f"repro_{trace_id or 'all'}_{ts}.zip")
    shutil.make_archive(zip_path[:-4], "zip", base)
    shutil.rmtree(base, ignore_errors=True)
    return zip_path

if __name__ == "__main__":
    import sys
    print(make_bundle(sys.argv[1] if len(sys.argv)>1 else None))
