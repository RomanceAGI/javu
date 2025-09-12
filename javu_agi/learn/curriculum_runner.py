from __future__ import annotations
import os, time, json
from typing import Dict, Any, List, Tuple
from javu_agi.learn.curriculum import Curriculum, Sampler, load_bank, update_result


def run_batch(
    exec_ctrl,
    cur: Curriculum,
    bank: Dict[str, List[Dict[str, Any]]] | None = None,
    batch: int = 8,
    write_prom: bool = True,
) -> List[Tuple[str, str, bool, float]]:
    if bank:
        load_bank(cur, bank)
    sp = Sampler(cur=cur, stage=cur.stage, batch=batch)
    items = sp.next_batch()
    metrics_dir = os.getenv("METRICS_DIR", "/data/metrics")
    os.makedirs(metrics_dir, exist_ok=True)
    prom = os.path.join(metrics_dir, "curriculum.prom")
    out: List[Tuple[str, str, bool, float]] = []
    for it in items:
        tag = (it.get("tags") or ["general"])[0]
        case_id = (
            it.get("id") or f"{tag}:{abs(hash(it.get('prompt',''))) & 0xffffffff:x}"
        )
        prompt = it.get("prompt", "").strip()
        t0 = time.time()
        res = exec_ctrl.process(user_id="bench", prompt=prompt)
        dt = time.time() - t0
        ok = bool(
            res
            and isinstance(res, dict)
            and res.get("status") in ("executed", "simulated")
            and not res.get("error")
        )
        update_result(cur, tag, case_id, ok, dt)
        out.append((tag, case_id, ok, dt))
        if write_prom:
            try:
                with open(prom, "a", encoding="utf-8") as f:
                    f.write(
                        f'curriculum_ok{{case="{case_id}",tag="{tag}"}} {1 if ok else 0}\n'
                    )
                    f.write(
                        f'curriculum_sec{{case="{case_id}",tag="{tag}"}} {dt:.4f}\n'
                    )
            except Exception:
                pass
    return out
