from __future__ import annotations
import os, time, json, threading, hashlib, hmac, base64
from dataclasses import dataclass
from typing import Any, Dict, Optional, Callable
import requests


# ---- Lightweight token bucket (per-user/per-adapter) ----
class _Bucket:
    def __init__(self, rps: float, burst: int = 5):
        self.rps = float(rps)
        self.burst = int(burst)
        self.tokens = self.burst
        self.last = time.monotonic()
        self.lock = threading.Lock()

    def take(self) -> None:
        with self.lock:
            now = time.monotonic()
            self.tokens = min(self.burst, self.tokens + (now - self.last) * self.rps)
            self.last = now
            if self.tokens < 1:
                sleep = (1 - self.tokens) / self.rps
                time.sleep(max(0.0, sleep))
                self.tokens = 0
            self.tokens -= 1


# ---- Simple circuit breaker ----
class _Breaker:
    def __init__(self, threshold: int = 5, cooldown_s: float = 30.0):
        self.fail = 0
        self.threshold = threshold
        self.cooldown_s = cooldown_s
        self.open_until = 0.0
        self.lock = threading.Lock()

    def allow(self) -> bool:
        with self.lock:
            return time.monotonic() >= self.open_until

    def ok(self):
        with self.lock:
            self.fail = 0

    def ko(self):
        with self.lock:
            self.fail += 1
            if self.fail >= self.threshold:
                self.open_until = time.monotonic() + self.cooldown_s
                self.fail = 0


# ---- Egress allowlist ----
def _host_allowed(url: str) -> bool:
    from urllib.parse import urlparse

    host = urlparse(url).hostname or ""
    allow = os.getenv("EGRESS_ALLOWLIST", "").split(",")
    allow = [h.strip().lower() for h in allow if h.strip()]
    if not allow:  # default deny unless explicit?
        return False
    host = host.lower()
    return any(host == a or host.endswith("." + a) for a in allow)


# ---- Redaction for audit logs ----
def _redact(d: Dict[str, Any]) -> Dict[str, Any]:
    out = {}
    for k, v in d.items():
        if k.lower() in ("authorization", "api_key", "token", "password"):
            out[k] = "***"
        elif isinstance(v, dict):
            out[k] = _redact(v)
        else:
            out[k] = v
    return out


@dataclass
class AdapterResult:
    ok: bool
    data: Any = None
    status: int = 200
    error: Optional[str] = None
    retries: int = 0
    cost_usd: float = 0.0
    latency_s: float = 0.0


class BaseAdapter:
    NAME = "base"
    RPS = 2.0
    BURST = 5
    TIMEOUT_S = 20.0
    RETRIES = 3
    BACKOFF_BASE = 0.6

    def __init__(
        self,
        http: Optional[requests.Session] = None,
        audit_hook: Optional[Callable] = None,
    ):
        self.http = http or requests.Session()
        self._bucket = _Bucket(self.RPS, self.BURST)
        self._brk = _Breaker()
        self.audit = audit_hook  # def (event:str, payload:dict) -> None

    # ---- HTTP helper with retry/backoff/allowlist/circuit ----
    def _http(self, method: str, url: str, **kw) -> AdapterResult:
        if not _host_allowed(url):
            return AdapterResult(False, status=451, error="egress_blocked")
        if not self._brk.allow():
            return AdapterResult(False, status=429, error="circuit_open")
        self._bucket.take()
        t0 = time.time()
        tries = 0
        last_err = None
        while tries <= self.RETRIES:
            tries += 1
            try:
                resp = self.http.request(method, url, timeout=self.TIMEOUT_S, **kw)
                if 200 <= resp.status_code < 300:
                    self._brk.ok()
                    lat = time.time() - t0
                    return AdapterResult(
                        True,
                        data=(
                            resp.json()
                            if "application/json"
                            in resp.headers.get("content-type", "")
                            else resp.text
                        ),
                        status=resp.status_code,
                        retries=tries - 1,
                        latency_s=round(lat, 3),
                    )
                # retryable?
                if resp.status_code in (408, 409, 425, 429, 500, 502, 503, 504):
                    raise RuntimeError(
                        f"retryable:{resp.status_code}:{resp.text[:200]}"
                    )
                # non-retryable
                self._brk.ko()
                return AdapterResult(
                    False,
                    status=resp.status_code,
                    error=resp.text[:500],
                    retries=tries - 1,
                    latency_s=round(time.time() - t0, 3),
                )
            except Exception as e:
                last_err = str(e)
                self._brk.ko()
                if tries > self.RETRIES:
                    break
                time.sleep(self.BACKOFF_BASE * (2 ** (tries - 1)) + (0.05 * tries))
        return AdapterResult(
            False,
            status=599,
            error=last_err or "request_failed",
            retries=tries - 1,
            latency_s=round(time.time() - t0, 3),
        )

    # ---- Audit helper ----
    def _audit(self, event: str, payload: Dict[str, Any]):
        if self.audit:
            try:
                self.audit(event, _redact(payload))
            except Exception:
                pass
