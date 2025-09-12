from __future__ import annotations
from typing import Dict, List
import hashlib, json, os, subprocess


class SupplyChainGuard:
    def __init__(self, sbom_path: str = "artifacts/sbom.json"):
        self.sbom_path = sbom_path
        os.makedirs(os.path.dirname(sbom_path), exist_ok=True)
        if not os.path.exists(sbom_path):
            json.dump({"files": []}, open(sbom_path, "w"))

    def _sha256(self, p: str) -> str:
        h = hashlib.sha256()
        with open(p, "rb") as f:
            for ch in iter(lambda: f.read(8192), b""):
                h.update(ch)
        return h.hexdigest()

    def record(self, path: str):
        sb = json.load(open(self.sbom_path))
        sb["files"] = [x for x in sb.get("files", []) if x["path"] != path]
        sb["files"].append({"path": path, "sha256": self._sha256(path)})
        json.dump(sb, open(self.sbom_path, "w"))

    def verify(self) -> Dict[str, List[str]]:
        sb = json.load(open(self.sbom_path))
        tampered = []
        for x in sb.get("files", []):
            try:
                if self._sha256(x["path"]) != x["sha256"]:
                    tampered.append(x["path"])
            except Exception:
                tampered.append(x["path"])
        return {"tampered": tampered}

    def pip_verify(self) -> Dict[str, List[str]]:
        try:
            out = subprocess.check_output(
                ["pip", "list", "--format", "json"], text=True
            )
            return {"pip": json.loads(out)}
        except Exception:
            return {"pip": []}
