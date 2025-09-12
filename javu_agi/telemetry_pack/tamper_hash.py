import os, json, hashlib


class TamperHasher:
    def __init__(self, salt_env: str = "TAMPER_SALT"):
        self._h = hashlib.sha256((os.getenv(salt_env, "") or "").encode("utf-8"))

    def feed(self, obj) -> None:
        try:
            b = json.dumps(obj, sort_keys=True, ensure_ascii=False).encode("utf-8")
            self._h.update(b)
        except Exception:
            pass

    def hexdigest(self) -> str:
        return self._h.hexdigest()

    try:
        from javu_agi.telemetry.hash_chain import HashChain

        chain = HashChain(self.metrics_dir)
        ch = chain.append(th.hexdigest())
        self.telemetry.emit("tamper_chain", {"chain_head": ch})
        self._write_metric("tamper_chain_len", {}, 1.0)  # indikator ada update
    except Exception:
        pass
