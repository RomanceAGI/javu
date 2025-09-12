"""
Small startup checks: ffmpeg presence, writable artifacts, optional Redis check.
Call javu_agi.startup_checks.run_all() at app init (or CI smoke).
"""
from __future__ import annotations
import shutil
import os
from javu_agi.utils.logger import get_logger
logger = get_logger("javu_agi.startup_checks")


def check_ffmpeg() -> bool:
    if shutil.which("ffmpeg") is None:
        logger.warning("ffmpeg not found in PATH; video/audio features may be degraded.")
        return False
    return True


def check_artifacts_writable(path: str = "artifacts") -> bool:
    try:
        os.makedirs(path, exist_ok=True)
        test = os.path.join(path, ".touch")
        with open(test, "w") as f:
            f.write("ok")
        os.remove(test)
        return True
    except Exception:
        logger.exception("Artifacts dir not writable: %s", path)
        return False


def check_redis(env_var: str = "REDIS_URL") -> bool:
    v = os.getenv(env_var, "")
    if not v:
        logger.info("No %s configured; skipping redis connectivity check", env_var)
        return True
    try:
        import redis as _redis  # type: ignore
        client = _redis.from_url(v, socket_timeout=2)
        client.ping()
        return True
    except Exception:
        logger.exception("Redis connectivity check failed for %s", v)
        return False


def run_all() -> dict:
    return {
        "ffmpeg": check_ffmpeg(),
        "artifacts_writable": check_artifacts_writable(),
        "redis_ok": check_redis(),
    }