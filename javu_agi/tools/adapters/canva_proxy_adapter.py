from __future__ import annotations
import os, requests
from typing import Dict, Any


class CanvaProxyAdapter:
    """
    Proxy aman ke backend lo sendiri (CANVA_PROXY_URL) yang sudah pegang OAuth Canva/App creds.
    Dengan cara ini, AGI tidak perlu tahu detail internal API Canva dan tetap compliant.
    """

    def __init__(self):
        self.base = os.getenv("CANVA_PROXY_URL", "").rstrip("/")
        self.token = os.getenv("CANVA_PROXY_TOKEN", "")

    def _hdr(self):
        if not self.base:
            return None, {"status": "error", "reason": "no_proxy_url"}
        h = {"Content-Type": "application/json"}
        if self.token:
            h["Authorization"] = f"Bearer {self.token}"
        return h, None

    def create_design(self, name: str, brief: str = "") -> Dict[str, Any]:
        h, err = self._hdr()
        if err:
            return err
        try:
            r = requests.post(
                f"{self.base}/canva/designs",
                headers=h,
                json={"name": name, "brief": brief},
                timeout=12,
            )
            return {
                "status": "ok" if r.ok else "error",
                "data": r.json(),
                "code": r.status_code,
            }
        except Exception as e:
            return {"status": "error", "reason": str(e)}

    def publish(self, design_id: str, destination: str = "drive") -> Dict[str, Any]:
        """
        destination contoh: 'drive' / 'gdrive' / 's3' — terserah implementasi proxy lo.
        """
        h, err = self._hdr()
        if err:
            return err
        try:
            r = requests.post(
                f"{self.base}/canva/designs/{design_id}/publish",
                headers=h,
                json={"destination": destination},
                timeout=20,
            )
            return {
                "status": "ok" if r.ok else "error",
                "data": r.json(),
                "code": r.status_code,
            }
        except Exception as e:
            return {"status": "error", "reason": str(e)}

    def list_designs(self, q: str = "", limit: int = 20) -> Dict[str, Any]:
        h, err = self._hdr()
        if err:
            return err
        try:
            r = requests.get(
                f"{self.base}/canva/designs",
                headers=h,
                params={"q": q, "limit": limit},
                timeout=10,
            )
            return {"status": "ok" if r.ok else "error", "data": r.json()}
        except Exception as e:
            return {"status": "error", "reason": str(e)}
