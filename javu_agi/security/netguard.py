import os, re, urllib.parse

_ALLOWED = None
_IP_RE = re.compile(r"^\d{1,3}(?:\.\d{1,3}){3}$")


def _load():
    global _ALLOWED
    if _ALLOWED is None:
        s = os.getenv("EGRESS_ALLOWLIST", "localhost,127.0.0.1")
        _ALLOWED = {h.strip().lower() for h in s.split(",") if h.strip()}
    return _ALLOWED


def egress_allow(url_or_cmd: str) -> bool:
    allowed = _load()
    u = (url_or_cmd or "").strip()
    if not u:
        return True
    if _IP_RE.match(u):
        return u in allowed
    if "://" in u:
        try:
            host = (urllib.parse.urlparse(u).hostname or "").lower()
            return any(host == a or host.endswith("." + a) for a in allowed)
        except Exception:
            return False
    return True
