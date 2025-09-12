import os, hmac, hashlib


def sign_line(line: str, key_env="AUDIT_HMAC_KEY") -> str:
    key = (os.getenv(key_env, "") or "").encode("utf-8")
    if not key:
        return line  # no-op jika kosong
    mac = hmac.new(key, line.encode("utf-8"), hashlib.sha256).hexdigest()
    return f"{line.rstrip()}\t#sig={mac}"
