"""
Safe subprocess helper: captures stdout/stderr, applies timeout, logs failures.
Use run_cmd([...]) instead of subprocess.run(...) directly.
"""
from __future__ import annotations
import subprocess
from typing import List, Optional, Dict, Any
from javu_agi.utils.logging_config import get_logger

logger = get_logger("javu_agi.subprocess_safe")


def run_cmd(
    cmd: List[str],
    cwd: Optional[str] = None,
    timeout: int = 30,
    check: bool = False,
    env: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """
    Run command safely and return dict with keys:
    {returncode, stdout, stderr, ok, error}
    Does not raise; callers should inspect returncode/ok.
    """
    try:
        p = subprocess.run(
            cmd,
            cwd=cwd,
            timeout=timeout,
            check=False,
            capture_output=True,
            text=True,
            env=env,
        )
        ok = p.returncode == 0
        if not ok:
            logger.warning("Command failed %s (code=%s). stdout:%s stderr:%s", cmd, p.returncode, (p.stdout or "")[:2000], (p.stderr or "")[:2000])
            if check:
                # mimic subprocess.check behavior but return error payload instead of raising
                return {"returncode": p.returncode, "stdout": p.stdout, "stderr": p.stderr, "ok": False, "error": f"non-zero exit {p.returncode}"}
        return {"returncode": p.returncode, "stdout": p.stdout or "", "stderr": p.stderr or "", "ok": ok, "error": None}
    except subprocess.TimeoutExpired as e:
        logger.exception("Command timeout: %s", cmd)
        return {"returncode": -1, "stdout": getattr(e, "stdout", "") or "", "stderr": getattr(e, "stderr", "") or "", "ok": False, "error": "timeout"}
    except Exception as e:
        logger.exception("Command exception: %s", cmd)
        return {"returncode": -1, "stdout": "", "stderr": "", "ok": False, "error": str(e)}