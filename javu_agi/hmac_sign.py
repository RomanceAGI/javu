import os, hmac, hashlib, time


def sign_cmd(cmd: str, ts: int | None = None) -> tuple[str, str]:
    secret = os.getenv("WORKER_HMAC_SECRET", "")
    if not secret:
        return "", ""
    ts = ts or int(time.time() * 1000)
    payload = f"{cmd}|{ts}".encode("utf-8")
    sig = hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()
    return str(ts), sig
