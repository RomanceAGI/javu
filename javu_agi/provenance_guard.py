import hashlib, os, json
import time
import shutil
from typing import Dict

TRUST_DIR = ".trusted_snapshots"

class ProvenanceGuard:
    """
    Menjaga jejak asal-usul artefak (model, config, tools).
    """
    def __init__(self, artifact_paths):
        self.paths = artifact_paths

    def _hash(self, path:str) -> str:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""): h.update(chunk)
        return h.hexdigest()

    def verify_artifacts(self) -> bool:
        meta_path = os.path.join(TRUST_DIR, "hashes.json")
        if not os.path.exists(meta_path): return True
        saved = json.load(open(meta_path))
        for p in self.paths:
            if self._hash(p) != saved.get(p,""): return False
        return True

    def snapshot(self, tag: str, meta: dict | None = None) -> None:
        """
        Create a trusted snapshot of the registered artifact paths.

        Copies each artifact into a timestamped file under the TRUSTED_SNAP_DIR and
        writes a ``latest.json`` metadata file describing the snapshot.  Existing
        files are overwritten.

        Parameters
        ----------
        tag : str
            A human‑readable label for the snapshot.
        meta : dict, optional
            Additional metadata to include (currently unused).
        """
        base = os.getenv("TRUSTED_SNAP_DIR", "/artifacts/trusted")
        os.makedirs(base, exist_ok=True)
        snap = {"tag": tag, "ts": int(time.time()), "files": {}}
        for p in (self.paths or []):
            if not os.path.exists(p):
                continue
            h = hashlib.sha256(open(p, "rb").read()).hexdigest()
            rel = f"{int(time.time())}_{os.path.basename(p)}"
            dst = os.path.join(base, rel)
            shutil.copy2(p, dst)
            snap["files"][p] = {"path": rel, "sha256": h}
        with open(os.path.join(base, "latest.json"), "w", encoding="utf-8") as f:
            json.dump(snap, f, ensure_ascii=False)

    def rollback_to_last_trusted(self) -> bool:
        """
        Restore artifacts from the most recent trusted snapshot.

        Returns
        -------
        bool
            True if rollback succeeded or there was no snapshot, False on error.
        """
        try:
            base = os.getenv("TRUSTED_SNAP_DIR", "/artifacts/trusted")
            latest = os.path.join(base, "latest.json")
            if not os.path.exists(latest):
                return False
            with open(latest, "r", encoding="utf-8") as f:
                snap = json.load(f)
            for p, meta in snap.get("files", {}).items():
                src = os.path.join(base, meta["path"])
                if os.path.exists(src):
                    os.makedirs(os.path.dirname(p), exist_ok=True)
                    shutil.copy2(src, p)
                    # verify hash
                    if hashlib.sha256(open(p, "rb").read()).hexdigest() != meta["sha256"]:
                        return False
            return True
        except Exception:
            return False

