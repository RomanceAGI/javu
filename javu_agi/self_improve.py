from __future__ import annotations
import os, json, time
from typing import Dict, Any

GENERATED_DIR = os.getenv("SKILL_CACHE_DIR", "/data/skills")


def _now_ms():
    return int(time.time() * 1000)


def propose_skill(desc: str, router, tools) -> Dict[str, Any]:
    """
    Sederhana: mapping deskripsi -> step tunggal yang bisa dieksekusi.
    """
    d = (desc or "").lower()
    if "csv" in d:
        return {
            "name": "csv_count_rows",
            "steps": [
                {
                    "tool": "python",
                    "cmd": "python - <<'PY'\nimport sys,csv\nr=csv.reader(sys.stdin)\nprint(sum(1 for _ in r))\nPY",
                }
            ],
        }
    if "http" in d or "url" in d:
        return {
            "name": "http_fetch_head",
            "steps": [{"tool": "bash", "cmd": 'curl -sI "$URL" | head -n 10'}],
        }
    return {
        "name": "echo_template",
        "steps": [
            {"tool": "bash", "cmd": 'echo "SKILL: ' + desc.replace('"', '\\"') + '"'}
        ],
    }


def verify_skill(skill: Dict[str, Any], exec_ctrl) -> bool:
    """Jalankan unit-test minimal: semua steps harus lolos verifier & eksekusi sandbox (sim / worker)."""
    worker = os.getenv("TOOL_WORKER_URL")
    if not worker:
        # Tanpa worker, rely on verifier strict saja
        for st in skill.get("steps", []):
            try:
                ok, _ = exec_ctrl.verify_step(
                    exec_ctrl.tools,
                    "sandbox://dry",
                    {"tool": st.get("tool"), "cmd": st.get("cmd"), "strict": True},
                    exec_ctrl.executor,
                )
            except Exception:
                ok = False
            if not ok:
                return False
        return True
    # Dengan worker: eksekusi nyata step pertama
    s0 = skill["steps"][0]
    ok, _ = exec_ctrl.verify_step(
        exec_ctrl.tools,
        worker,
        {"tool": s0["tool"], "cmd": s0["cmd"], "strict": True},
        exec_ctrl.executor,
    )
    if not ok:
        return False
    res = exec_ctrl.tools.run_remote(s0["cmd"], worker)
    return int(res.get("code", -1)) == 0


def register_skill(skill: Dict[str, Any]) -> str:
    """Simpan ke SKILL_CACHE_DIR agar bisa dipakai composer/graph; format JSON generik."""
    os.makedirs(GENERATED_DIR, exist_ok=True)
    name = skill.get("name") or f"gen_{_now_ms()}"
    path = os.path.join(GENERATED_DIR, f"{name}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(skill, f, ensure_ascii=False, indent=2)
    return path
