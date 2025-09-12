from __future__ import annotations
from typing import Dict, Any
import threading

# STRICT absolute imports (hindari import cycle/relatif)
from javu_agi.executive_controller import ExecutiveController
from javu_agi.loop_guard import safe_loop

# ---- lazy singleton untuk controller (hindari heavy init berulang) ----
_EXEC: ExecutiveController | None = None
_EXEC_LOCK = threading.Lock()


def _get_exec() -> ExecutiveController:
    global _EXEC
    if _EXEC is None:
        with _EXEC_LOCK:
            if _EXEC is None:
                _EXEC = ExecutiveController()
    return _EXEC


@safe_loop(timeout_s=25)
def run_core_loop(user_id: str, full_input: str) -> Dict[str, Any]:
    """
    Satu siklus kognitif.
    Return format stabil untuk UI/API:
    {
      "user_id": ..., "input": ..., "response": ..., "meta": {...}
    }
    """
    execu = _get_exec()
    try:
        response, meta = execu.process(user_id, full_input)
        return {
            "user_id": user_id,
            "input": full_input,
            "response": response,
            "meta": meta,
        }
    except Exception as e:
        return {
            "user_id": user_id,
            "input": full_input,
            "response": f"[ERROR] {e}",
            "meta": {"error": True},
        }


# Kompat alias untuk kode lama
def run_user_loop(user_id: str, full_input: str) -> str:
    return run_core_loop(user_id, full_input)["response"]


if __name__ == "__main__":
    out = run_core_loop(
        "alpha", "Rancang hipotesis baru tentang materi gelap secara ringkas."
    )
    print(out["response"])
