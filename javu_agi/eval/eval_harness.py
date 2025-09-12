import os, json, time, argparse
import datetime as _dt
from pathlib import Path
from typing import Dict, List, Any

from javu_agi.utils.metrics_server import set_metric
from javu_agi.rag.retriever import RagRetriever
from javu_agi.eval.validators import validate_answer

# singleton RAG retriever (hemat instansiasi per task)
_RAG = RagRetriever()


# --------- optional imports (graceful) ----------
def _try_import(path):
    try:
        mod = __import__(path, fromlist=["*"])
        return mod
    except Exception:
        return None


EC_mod = _try_import("javu_agi.executive_controller")
TB_mod = _try_import("javu_agi.arena.task_bank")


# --------- utils ----------
def now_ts() -> int:
    return int(time.time())


def write_json(p: str, obj: Any):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False)


def read_latest_metrics(default: Dict[str, Any] | None = None) -> Dict[str, Any]:
    p = Path("arena_logs/daily/latest.json")
    if p.exists():
        try:
            return json.loads(p.read_text())
        except Exception:
            pass
    return default or {}


def write_fail_cases(
    per_task: List[Dict[str, Any]], out="arena_logs/daily/fail_cases.json", topk=500
):
    """Simpan hanya kasus gagal (sorted by 'difficulty' kalau ada)."""
    if not per_task:
        return
    fails = [r for r in per_task if not r.get("success", False)]
    # sort opsional kalau ada 'difficulty'
    fails.sort(key=lambda r: r.get("difficulty", 0.0), reverse=True)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        for r in fails[:topk]:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


# --------- core evaluation ----------
def _load_eval_list(subset: str) -> List[Dict[str, Any]]:
    """
    Ambil daftar task untuk subset: 'arena' | 'transfer' | 'adversarial'.
    Prioritas: task_bank API -> fallback ke JSONL konvensi.
    Return: list[dict] task (tiap dict minimal punya id/query/answer/type)
    """
    paths = {
        "arena": "data/banks/arena_eval.jsonl",
        "transfer": "data/banks/transfer_eval.jsonl",
        "adversarial": "data/banks/adversarial_eval.jsonl",
    }

    # 1) kalau ada task_bank module dengan API load_eval_items, pakai itu
    if TB_mod and hasattr(TB_mod, "load_eval_items"):
        return TB_mod.load_eval_items(subset)  # type: ignore

    # 2) fallback: baca JSONL
    p = Path(paths.get(subset, paths["arena"]))
    if not p.exists():
        return []

    items: List[Dict[str, Any]] = []
    with p.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
                # normalisasi minimal field
                task = {
                    "id": rec.get("id") or rec.get("task_id"),
                    "type": rec.get("type", "qa"),
                    "query": rec.get("query") or rec.get("prompt") or "",
                    "answer": rec.get("answer") or rec.get("gold") or "",
                }
                items.append(task)
            except Exception:
                # skip baris rusak
                continue
    return items


def _exec_once(controller, task):
    t0 = time.time()
    try:
        query = task.get("query") or task.get("prompt") or ""

        # RAG context via singleton
        rag_docs = _RAG.retrieve(query, k=5)
        ctx_texts = [d.get("text", "") for d in rag_docs]

        # bentuk input kaya konteks
        enriched = {"query": query, "context": ctx_texts}

        # panggil controller (process / execute)
        if hasattr(controller, "process"):
            out = controller.process("eval", enriched)
        else:
            out = controller.execute("eval", enriched)

        text = (
            (out[0] if isinstance(out, tuple) else out.get("text", "")) if out else ""
        )
        meta = (
            (out[1] if isinstance(out, tuple) else out.get("meta", {})) if out else {}
        )
        if not isinstance(meta, dict):
            meta = {}

        # atribusi retrieval ke meta
        meta.setdefault(
            "retrieval_attrib",
            [
                {
                    "source": d.get("source", "corpus"),
                    "score": float(d.get("score", 0.0)),
                }
                for d in rag_docs
            ],
        )
        meta["latency_s"] = round(time.time() - t0, 3)

        # validasi task-aware
        check = validate_answer(task, text, meta)
        meta["validation"] = check

        return {
            "text": text,
            "meta": meta,
            "success": bool(check["success"]),
            "reward": float(check["reward"]),
            "reason": check.get("reason", ""),
        }
    except Exception as e:
        return {
            "text": "",
            "meta": {"error": str(e)},
            "success": False,
            "reward": 0.0,
            "reason": "exception",
        }


def _aggregate(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    n = max(1, len(rows))
    sr = sum(1.0 if r.get("success") else 0.0 for r in rows) / n
    avg_r = sum(r.get("reward", 0.0) for r in rows) / n
    avg_l = sum((r.get("meta") or {}).get("latency_s", 0.0) for r in rows) / n
    avg_cost = sum(float((r.get("meta") or {}).get("cost_usd", 0.0)) for r in rows) / n
    avg_v = (
        sum(
            float(((r.get("meta") or {}).get("verifier") or {}).get("score", 0.0))
            for r in rows
        )
        / n
    )
    return {
        "n": len(rows),
        "success_rate": sr,
        "avg_reward": avg_r,
        "avg_latency_s": avg_l,
        "avg_cost_usd": avg_cost,
        "avg_verifier": avg_v,
    }


def run_eval_subset(
    subset: str = "arena",
    write_json_path: str | None = None,
    limit: int = 200,
    suite: str = "default",
) -> Dict[str, Any]:
    tasks = _load_eval_list(subset)[:limit]
    run_date = _dt.datetime.utcnow().strftime("%Y-%m-%d")
    if not (EC_mod and hasattr(EC_mod, "ExecutiveController")):
        raise RuntimeError(
            "ExecutiveController not found: javu_agi.executive_controller"
        )

    # eksekusi
    rows: List[Dict[str, Any]] = []
    if EC_mod and hasattr(EC_mod, "ExecutiveController"):
        ec = EC_mod.ExecutiveController()  # type: ignore
        rows = [_exec_once(ec, t) for t in tasks]

    # per-task output kaya (untuk jsonl + failcases)
    items: List[Dict[str, Any]] = []
    for t, out in zip(tasks, rows):
        meta = out.get("meta", {}) or {}
        items.append(
            {
                "id": t.get("id"),
                "suite": suite,
                "date": run_date,
                "prompt": t.get("query") or t.get("prompt"),
                "answer": out.get("text", ""),
                "gold": t.get("answer"),
                "success": out.get("success", False),
                "reward": out.get("reward", 0.0),
                "time_s": meta.get("latency_s", 0.0),
                "cost_usd": float(meta.get("cost_usd", 0.0)),
                "verifier": meta.get("verifier", {}),
                "retrieval_attrib": meta.get("retrieval_attrib", []),
                "used_tools": meta.get("tools", []),
            }
        )

    # agregasi
    agg = _aggregate(rows)
    metrics = {
        "suite": suite,
        "subset": subset,
        "date": run_date,
        "ts": now_ts(),
        "n": agg["n"],
        "success_rate": agg["success_rate"],
        "avg_reward": agg["avg_reward"],
        "avg_latency_s": agg["avg_latency_s"],
        "avg_cost_usd": agg["avg_cost_usd"],
        "avg_verifier": agg["avg_verifier"],
    }

    # tulis file (json agregat + jsonl per-task + failcases)
    out_dir = f"logs/eval/{run_date}"
    os.makedirs(out_dir, exist_ok=True)
    if write_json_path:
        write_json(write_json_path, metrics)
    with open(f"{out_dir}/{suite}_{subset}.jsonl", "w", encoding="utf-8") as fo:
        for it in items:
            fo.write(json.dumps(it, ensure_ascii=False) + "\n")
    write_fail_cases(items, f"{out_dir}/failcases_{suite}_{subset}.jsonl")

    # push ke metrics server (opsional; aman kalau no-op)
    try:
        set_metric("eval_success_rate", metrics["success_rate"])
        set_metric("eval_latency_avg_s", metrics["avg_latency_s"])
        set_metric("eval_cost_avg_usd", metrics["avg_cost_usd"])
    except Exception:
        pass

    return metrics


# --------- CLI ----------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--suite", default="default")
    ap.add_argument(
        "--subset", default="arena", choices=["arena", "transfer", "adversarial"]
    )
    ap.add_argument("--limit", type=int, default=200)
    ap.add_argument("--write_json", default="arena_logs/daily/latest.json")
    ap.add_argument("--schedule", choices=["once", "daily"], default="once")
    args = ap.parse_args()

    if args.schedule == "once":
        run_eval_subset(args.subset, args.write_json, args.limit, suite=args.suite)
        print(f"[eval] wrote {args.write_json}")
        return

    # daily loop
    while True:
        out = run_eval_subset(
            "arena", "arena_logs/daily/latest.json", args.limit, suite=args.suite
        )
        # rotate by date
        datep = f"arena_logs/daily/{time.strftime('%Y-%m-%d')}.json"
        write_json(datep, out)
        print(f"[eval-daily] {datep}")
        time.sleep(24 * 3600)


if __name__ == "__main__":
    main()
