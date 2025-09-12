from __future__ import annotations
import json, time, random
from typing import List, Dict, Any, Tuple
from javu_agi.executive_controller import ExecutiveController


def _run(exec: ExecutiveController, user: str, q: str) -> Dict[str, Any]:
    out, meta = exec.process(user, q)
    return {"resp": out, "meta": meta}


def _toggle_ctx(exec: ExecutiveController, on: bool):
    # enable/disable contextual learner dinamis via flag instance
    exec.learner_ctx = exec.learner_ctx if on else None


def run_rct(queries: List[str], seed: int = 7, per_arm: int = 20) -> Dict[str, Any]:
    random.seed(seed)
    exec = ExecutiveController()
    A, B = [], []
    picked = random.sample(queries, min(len(queries), per_arm * 2))
    groupA = picked[:per_arm]  # Contextual ON
    groupB = picked[per_arm : per_arm * 2]  # Contextual OFF

    t0 = time.time()
    _toggle_ctx(exec, True)
    for q in groupA:
        A.append(_run(exec, "rctA", q))

    _toggle_ctx(exec, False)
    for q in groupB:
        B.append(_run(exec, "rctB", q))
    dt = round(time.time() - t0, 2)

    def _agg(rows):
        if not rows:
            return {}
        r = [x["meta"]["reward"] for x in rows]
        lat = [x["meta"]["latency_s"] for x in rows]
        conf = [x["meta"].get("chosen_confidence", 0.0) for x in rows]
        return {
            "n": len(rows),
            "avg_reward": sum(r) / len(r),
            "avg_latency": sum(lat) / len(lat),
            "avg_confidence": sum(conf) / len(conf),
        }

    return {
        "elapsed_s": dt,
        "A_ctx_on": _agg(A),
        "B_ctx_off": _agg(B),
        "uplift_reward": (_agg(A).get("avg_reward", 0) - _agg(B).get("avg_reward", 0)),
        "uplift_confidence": (
            _agg(A).get("avg_confidence", 0) - _agg(B).get("avg_confidence", 0)
        ),
    }


if __name__ == "__main__":
    # contoh queries ringan; ganti dengan dataset lo
    qs = [
        "Jelaskan singkat mengapa langit biru.",
        "Urutkan angka: 5,2,9,1",
        "Hipotesis tentang materi gelap dan rotasi galaksi.",
        "Formatkan bullet tentang fotosintesis.",
        "Dampak jika gravitasi meningkat 10%.",
        "Analisis pasar: harga gandum naik 5%, implikasinya?",
        "Tulis fungsi python untuk balik string.",
    ]
    print(json.dumps(run_rct(qs, per_arm=3), indent=2))
