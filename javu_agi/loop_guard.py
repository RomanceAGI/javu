from __future__ import annotations
import threading, functools, time
import os


class TimeoutError(Exception):
    pass


def safe_loop(timeout_s: int = None, on_timeout: str = "[TIMEOUT]"):
    """
    Jalankan fn di thread daemon + join timeout.
    - Soft-timeout, cross-platform.
    - Propagate exception dari fn.
    """
    if timeout_s is None:
        timeout_s = int(os.getenv("CORE_LOOP_TIMEOUT_S", "25"))

    def deco(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            result = {}
            err = {}

            def target():
                try:
                    result["v"] = fn(*args, **kwargs)
                except Exception as e:
                    err["e"] = e

            t = threading.Thread(target=target, daemon=True)
            t.start()
            t.join(timeout_s)
            if t.is_alive():
                # biar thread berhenti sendiri; kita fail fast di caller
                raise TimeoutError(f"{on_timeout} exceeded {timeout_s}s")
            if "e" in err:
                raise err["e"]
            return result.get("v")

        return wrapper

    return deco
