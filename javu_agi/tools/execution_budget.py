from __future__ import annotations


class ExecutionBudget:
    """
    Batas eksekusi per episode:
    - max_steps
    - max_errors (circuit breaker)
    """

    def __init__(self, max_steps: int = 8, max_errors: int = 2):
        self.max_steps = max_steps
        self.max_errors = max_errors

    def allow(self, step_idx: int, errors: int) -> bool:
        if step_idx >= self.max_steps:
            return False
        if errors > self.max_errors:
            return False
        return True
