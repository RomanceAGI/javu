from __future__ import annotations
import os, json, time, uuid
from typing import List, Dict, Any
import requests

API = os.getenv("EVAL_API", "http://localhost:8080")
API_KEY = os.getenv("API_KEY", "devkey")

TASKS: List[Dict[str, Any]] = [
    {"mode": "qna", "query": "Ringkas berita gempa 5 poin dan rekomendasi darurat."},
    {"mode": "qna", "query": "Jelaskan konsep backpropagation ke siswa SMA."},
    {
        "mode": "qna",
        "query": "Rancang diet 7 hari untuk penderita diabetes (umum, bukan medis).",
    },
    {
        "mode": "codegen",
        "spec": "Python: fungsi parse CSV besar stream-friendly + unit test.",
    },
    {"mode": "codegen", "spec": "SQL: query agregasi cohort retention bulanan."},
    {
        "mode": "automate",
        "goal": "Ambil 3 email terbaru & jadwalkan follow-up di kalender.",
    },
    {
        "mode": "automate",
        "goal": "Cari 5 file ‘proposal’ di Drive dan kirim ringkasan ke Slack.",
    },
    {"mode": "qna", "query": "Debat pro-kontra nuklir: ringkas 10 poin, netral."},
    {"mode": "qna", "query": "Strategi mitigasi banjir perkotaan ramah lingkungan."},
    {"mode": "codegen", "spec": "Buat FastAPI endpoint /metrics + test."},
    {"mode": "qna", "query": "Rencana proyek AI literasi digital untuk desa, 6 bulan."},
    {"mode": "qna", "query": "Rancang kurikulum etika AI untuk SMA 4 pertemuan."},
    {"mode": "qna", "query": "Dokumentasi arsitektur AGI lo: 10 poin utama."},
    {"mode": "qna", "query": "Buat poster ajakan damai (teks saja) bilingual ID-EN."},
    {"mode": "automate", "goal": "Posting pengumuman ke Discord & Teams serentak."},
]


def call_api(task: Dict[str, Any]) -> Dict[str, Any]:
    headers = {"x-api-key": API_KEY, "Content-Type": "application/json"}
    if task["mode"] == "qna":
        r = requests.post(
            f"{API}/v0/qna",
            headers=headers,
            json={"query": task["query"], "context": ""},
            timeout=60,
        )
    elif task["mode"] == "codegen":
        r = requests.post(
            f"{API}/v0/codegen",
            headers=headers,
            json={"spec": task["spec"]},
            timeout=120,
        )
    elif task["mode"] == "automate":
        r = requests.post(
            f"{API}/v0/automate",
            headers=headers,
            json={"goal": task["goal"], "constraints": []},
            timeout=180,
        )
    else:
        return {"status": "error", "reason": "unknown_mode"}
    try:
        return r.json()
    except Exception:
        return {"status": "error", "reason": "bad_json", "text": r.text}


def heuristic_score(resp: Dict[str, Any]) -> float:
    # skoring dummy: status ok + panjang output + tidak terblokir
    if not isinstance(resp, dict):
        return 0.0
    if resp.get("status") not in {"ok", "executed", "success"}:
        return 0.2
    text = json.dumps(resp)[:5000]
    L = len(text)
    if "blocked" in text or "deny" in text:
        return 0.5
    return min(1.0, 0.3 + (L / 5000) * 0.7)


def main():
    rid = f"eval_{int(time.time())}"
    out_dir = os.getenv("EVAL_DIR", "artifacts/evals")
    os.makedirs(out_dir, exist_ok=True)
    results = []
    for i, task in enumerate(TASKS, 1):
        t0 = time.time()
        resp = call_api(task)
        dt = time.time() - t0
        score = heuristic_score(resp)
        results.append(
            {
                "i": i,
                "task": task,
                "resp_status": resp.get("status"),
                "latency_s": round(dt, 3),
                "score": round(score, 3),
            }
        )
        with open(f"{out_dir}/{rid}.jsonl", "a", encoding="utf-8") as f:
            f.write(
                json.dumps(
                    {"task": task, "resp": resp, "latency_s": dt, "score": score},
                    ensure_ascii=False,
                )
                + "\n"
            )
        print(
            f"[{i:02d}] {task['mode']} score={score:.3f} t={dt:.2f}s status={resp.get('status')}"
        )
    # ringkasan
    avg = sum(r["score"] for r in results) / len(results)
    summ = {
        "run_id": rid,
        "avg_score": round(avg, 3),
        "n": len(results),
        "results": results,
    }
    with open(f"{out_dir}/{rid}_summary.json", "w", encoding="utf-8") as f:
        json.dump(summ, f, ensure_ascii=False, indent=2)
    print("Avg score:", round(avg, 3), "saved:", f"{out_dir}/{rid}_summary.json")


if __name__ == "__main__":
    import os

    main()
