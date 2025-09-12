from __future__ import annotations
from typing import List, Dict

class PlanOptimizer:
    """
    Optimizer langkah:
    - Dedup perintah identik
    - Fuse langkah python berturut-turut jadi satu script (hemat call)
    - Truncate hingga max_steps
    """
    def __init__(self, max_steps: int = 8):
        self.max_steps = max_steps

    def optimize(self, steps: List[Dict]) -> List[Dict]:
        """
        Optimize a list of plan steps by deduplicating and fusing consecutive python commands.

        Duplicate tool/cmd pairs are removed while preserving order. Consecutive
        python steps are merged into a single multi-line script wrapped in a
        ``python - <<'PY' ... PY`` heredoc to reduce tool invocations. Non-python
        steps flush any accumulated python buffer.

        Parameters
        ----------
        steps : List[Dict]
            A list of plan step dictionaries. Each step should have ``tool`` and ``cmd`` keys.

        Returns
        -------
        List[Dict]
            The optimized list of steps, truncated to ``self.max_steps``.
        """
        # Remove duplicate tool/cmd pairs while preserving order
        seen = set()
        dedup: List[Dict] = []
        for s in steps:
            sig = (s.get("tool", ""), s.get("cmd", ""))
            if sig in seen:
                continue
            seen.add(sig)
            dedup.append(s)

        # Buffer for fusing python commands
        fused: List[Dict] = []
        buf: List[str] = []

        def _flush() -> None:
            nonlocal buf, fused
            if buf:
                code = "\n\n".join(buf)
                fused.append({"tool": "python", "cmd": f"python - <<'PY'\n{code}\nPY"})
                buf = []

        for s in dedup:
            tool = s.get("tool", "")
            cmd = s.get("cmd", "") or ""
            if tool == "python" and cmd.startswith("python - <<'PY'"):
                # Extract body safely
                try:
                    head = "python - <<'PY'\n"
                    tail = "\nPY"
                    start = cmd.index(head) + len(head)
                    end = cmd.rindex(tail)
                    body = cmd[start:end]
                except ValueError:
                    body = cmd
                buf.append(body.strip())
            elif tool == "python":
                buf.append(f"print({repr(cmd)})")
            else:
                _flush()
                fused.append(s)
        _flush()
        return fused[: self.max_steps]
