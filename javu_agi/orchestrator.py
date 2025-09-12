from __future__ import annotations
import time, threading
from dataclasses import dataclass
from typing import List, Dict, Optional, Callable


@dataclass
class SubTask:
    title: str
    input_text: str
    budget_usd: float
    timeout_s: float = 60.0


@dataclass
class SubResult:
    ok: bool
    text: str
    meta: Dict


class AgentOrchestrator:
    def __init__(
        self, spawn_fn: Callable[[str, str], tuple[str, dict]], max_parallel: int = 3
    ):
        """
        spawn_fn(user_id, text) -> (response, meta)  # re-enter EC with same tuple contract
        """
        self.spawn_fn = spawn_fn
        self.max_parallel = max_parallel

    def run(self, user_id: str, subtasks: List[SubTask]) -> List[SubResult]:
        # simple bounded parallelism
        out: List[SubResult] = [None] * len(subtasks)  # type: ignore
        lock = threading.Lock()
        idx = 0

        def worker():
            nonlocal idx
            while True:
                with lock:
                    if idx >= len(subtasks):
                        return
                    i = idx
                    idx += 1
                st = subtasks[i]
                t0 = time.time()
                try:
                    # NOTE: budget enforcement per subtask dilakukan di EC cost_guard (already per-user daily)
                    resp, meta = self.spawn_fn(
                        user_id, f"[Subtask:{st.title}] {st.input_text}"
                    )
                    out[i] = SubResult(
                        ok=not meta.get("blocked", False), text=resp, meta=meta
                    )
                except Exception as e:
                    out[i] = SubResult(ok=False, text="", meta={"error": str(e)})
                if time.time() - t0 > st.timeout_s:
                    out[i].ok = False
                    out[i].meta["timeout"] = True

        threads = [
            threading.Thread(target=worker, daemon=True)
            for _ in range(min(self.max_parallel, len(subtasks)))
        ]
        [t.start() for t in threads]
        [t.join() for t in threads]
        return out  # list of SubResult
