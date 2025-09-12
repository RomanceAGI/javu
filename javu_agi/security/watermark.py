import os, hmac, hashlib, base64, time

_SECRET = os.getenv("WATERMARK_SECRET", "changeme").encode("utf-8")


def sign_output(text: str, meta: dict | None = None) -> str:
    msg = (text or "").encode("utf-8")
    ts = str(int(time.time()))
    tag = hmac.new(_SECRET, msg + ts.encode("utf-8"), hashlib.sha256).digest()
    sig = base64.urlsafe_b64encode(tag).decode().rstrip("=")
    return f"{text}\n\n<!-- wm:{ts}:{sig} -->"


def verify_input(text: str, max_age_s: int = 3600) -> bool:
    if not text:
        return False
    if "<!-- wm:" not in text:
        return False
    try:
        ts = text.split("<!-- wm:", 1)[1].split(":", 1)[0]
        sig = text.split("<!-- wm:", 1)[1].split(":", 2)[1].split("-->", 1)[0].strip()
        body = text.split("<!-- wm:", 1)[0].encode("utf-8")
        tag = hmac.new(_SECRET, body + ts.encode("utf-8"), hashlib.sha256).digest()
        expect = base64.urlsafe_b64encode(tag).decode().rstrip("=")
        if not hmac.compare_digest(expect, sig):
            return False
        if (int(time.time()) - int(ts)) > max_age_s:
            return False
        return True
    except Exception:
        return False
