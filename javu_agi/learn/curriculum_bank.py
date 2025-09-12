from __future__ import annotations
import os, json, re, time, random, hashlib
from pathlib import Path
from typing import Dict, Any, List, Optional

TRACE_DIR = "trace/logs"
BANK_DIR = "data/task_bank"
os.makedirs(BANK_DIR, exist_ok=True)


def _norm(s: str) -> str:
    return (s or "").strip()


def _hash(d: Dict[str, Any]) -> str:
    h = hashlib.sha256(
        json.dumps(d, sort_keys=True).encode("utf-8", "ignore")
    ).hexdigest()
    return h[:16]


def _mk_rule_from_text(text: str) -> Dict[str, Any]:
    """
    Heuristik bikin rule evaluasi minimal:
    - kalau ada angka berturut → regex urutan
    - else: contains kata kunci (3–10 char)
    """
    t = (text or "").strip()
    nums = re.findall(r"\d+", t)
    if len(nums) >= 3:
        # contoh: "1 2 5 9" -> regex urutan
        patt = ".*".join(map(re.escape, nums[:6]))
        return {"check": "regex", "value": patt}
    # fallback contains dari kata kunci
    toks = [w for w in re.findall(r"[a-zA-Z0-9_]+", t) if 3 <= len(w) <= 12]
    if toks:
        return {"check": "contains", "value": toks[0]}
    return {"check": "contains", "value": t[:16]}


def _infer_tags(prompt: str) -> List[str]:
    p = prompt.lower()
    tags = []
    if any(k in p for k in ["urut", "sort", "format", "ringkas"]):
        tags.append("plan")
    if any(k in p for k in ["jumlah", "kali", "bagi", "persen", "angka", "soal"]):
        tags.append("math")
    if any(k in p for k in ["kode", "python", "algoritma", "fungsi"]):
        tags.append("code")
    if any(
        k in p for k in ["fisika", "energi", "materi", "kuantum", "galaksi", "gelap"]
    ):
        tags.append("science")
    if not tags:
        tags.append("general")
    return tags


def mine_from_episode_dir(user: str, ep: str) -> Optional[Dict[str, Any]]:
    """
    Ambil 1 task dari episode yang gagal/kurang bagus:
    - baca SELECT (chosen), REWARD (shaped), THOUGHTS
    - jika reward < 0.35 → jadikan task dengan rule dari 'jawaban benar proxy' (draft terbaik lain) atau dari chosen
    """
    base = Path(TRACE_DIR) / user / ep
    if not base.exists():
        return None
    G = base / "graph.jsonl"
    if not G.exists():
        return None

    nodes = [
        json.loads(x) for x in G.read_text(encoding="utf-8").splitlines() if x.strip()
    ]
    select = [n for n in nodes if n.get("t") == "NODE" and n.get("kind") == "SELECT"]
    reward = [n for n in nodes if n.get("t") == "NODE" and n.get("kind") == "REWARD"]
    thought = [n for n in nodes if n.get("t") == "NODE" and n.get("kind") == "THOUGHT"]

    if not select or not reward:
        return None
    shaped = float((reward[-1].get("content") or {}).get("shaped", 0.0))
    if shaped >= 0.35:  # hanya ambil kasus lemah
        return None

    choice = (select[-1].get("content") or {}).get("choice") or {}
    chosen_text = str(choice.get("text", "")).strip()
    # proxy jawaban “lebih baik”: cari draft dengan sim confidence tertinggi
    best_alt = None
    for n in thought:
        draft = (n.get("content") or {}).get("draft", "")
        if len(draft) > len(chosen_text):  # heuristik sederhana
            best_alt = draft
    truth_proxy = best_alt or chosen_text
    if not truth_proxy:
        return None

    # reconstruct prompt (ada di meta awal episode)
    meta = Path(TRACE_DIR) / user / ep / "meta.json"
    if meta.exists():
        m = json.loads(meta.read_text(encoding="utf-8"))
        prompt = m.get("prompt", "")
    else:
        prompt = ""

    if not prompt:
        return None

    rule = _mk_rule_from_text(truth_proxy)
    task = {
        "prompt": _norm(prompt),
        "rule": rule,
        "tags": _infer_tags(prompt),
        "source": {"user": user, "episode": ep, "reward": shaped},
    }
    task["id"] = _hash({"p": task["prompt"], "r": task["rule"]})
    return task


def sweep_traces(limit: int = 500) -> List[Dict[str, Any]]:
    out = []
    root = Path(TRACE_DIR)
    if not root.exists():
        return out
    for user in os.listdir(root):
        udir = root / user
        if not udir.is_dir():
            continue
        for ep in os.listdir(udir):
            if len(out) >= limit:
                break
            t = mine_from_episode_dir(user, ep)
            if t:
                out.append(t)
    return out


def save_to_bank(
    tasks: List[Dict[str, Any]], bank_name: str = "auto_hard.jsonl"
) -> int:
    path = Path(BANK_DIR) / bank_name
    seen = set()
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            try:
                seen.add(json.loads(line).get("id"))
            except Exception:
                pass
    n = 0
    with path.open("a", encoding="utf-8") as f:
        for t in tasks:
            if t["id"] in seen:
                continue
            f.write(json.dumps(t, ensure_ascii=False) + "\n")
            seen.add(t["id"])
            n += 1
    return n


def generate(
    limit_sweep: int = 500, bank_name: str = "auto_hard.jsonl"
) -> Dict[str, Any]:
    tasks = sweep_traces(limit=limit_sweep)
    random.shuffle(tasks)
    n = save_to_bank(tasks, bank_name=bank_name)
    return {
        "found": len(tasks),
        "new_saved": n,
        "bank": str(Path(BANK_DIR) / bank_name),
    }


CURR_APPEND = [
    # --- ENVIRONMENT / ENERGY CLEAN ---
    {
        "id": "clean_energy_roadmap_v1",
        "tier": 2,
        "domain": "environment",
        "goal": "Susun roadmap 90 hari pengurangan emisi listrik kantor 30% dgn biaya rendah.",
        "tools_needed": ["search", "code", "spreadsheet", "shell"],
        "constraints": ["no_pii", "budget_usd<=100", "cite_sources>=3"],
        "success_criteria": [
            "deliverable:plan_markdown",
            "kpi:emission_reduction>=0.30",
            "kpi:cost<=100",
            "safety:pii=0",
        ],
        "max_steps": 12,
    },
    {
        "id": "microgrid_feasibility_v1",
        "tier": 3,
        "domain": "environment",
        "goal": "Studi kelayakan microgrid tenaga surya untuk desa 500 KK; output tabel + analisa risiko.",
        "tools_needed": ["search", "code", "spreadsheet"],
        "constraints": ["no_pii", "include_env_impact", "include_maintenance_cost"],
        "success_criteria": [
            "deliverable:feasibility_report",
            "table:capex_opex",
            "risk_register>=8",
            "safety:pii=0",
        ],
        "max_steps": 14,
    },
    {
        "id": "plastic_waste_90d_v1",
        "tier": 1,
        "domain": "environment",
        "goal": "Rencana pengurangan sampah plastik 25% dalam 90 hari (kantor).",
        "tools_needed": ["search", "spreadsheet"],
        "constraints": ["no_pii", "stakeholder_map"],
        "success_criteria": [
            "deliverable:action_list",
            "kpi:reduction>=0.25",
            "safety:pii=0",
        ],
        "max_steps": 8,
    },
    # --- HEALTH (NON-DIAGNOSTIC) ---
    {
        "id": "health_info_access_v1",
        "tier": 2,
        "domain": "health_info",
        "goal": "Desain portal informasi kesehatan non-diagnostik dgn kebijakan privasi kuat.",
        "tools_needed": ["search", "code"],
        "constraints": ["no_medical_advice", "no_pii", "privacy_policy_section"],
        "success_criteria": [
            "deliverable:spec_md",
            "policy:privacy_ok",
            "safety:pii=0",
        ],
        "max_steps": 10,
    },
    {
        "id": "vaccination_campaign_ethics_v1",
        "tier": 2,
        "domain": "public_health",
        "goal": "Rencana kampanye edukasi vaksin etis, anti-hoax, berbasis bukti.",
        "tools_needed": ["search"],
        "constraints": ["no_pii", "cite_sources>=5", "no_persuasion_targeting"],
        "success_criteria": [
            "deliverable:communication_plan",
            "safety:policy_ok",
            "safety:pii=0",
        ],
        "max_steps": 9,
    },
    # --- EDUCATION / PEACEBUILDING ---
    {
        "id": "ai_ethics_curriculum_hs_v1",
        "tier": 3,
        "domain": "education",
        "goal": "Kurikulum AI etis untuk siswa SMA (8 minggu).",
        "tools_needed": ["search", "code"],
        "constraints": ["include_learning_objectives", "assessment_rubric"],
        "success_criteria": ["deliverable:silabus", "rubric>=1", "safety:policy_ok"],
        "max_steps": 12,
    },
    {
        "id": "community_anti_hoax_v1",
        "tier": 2,
        "domain": "peacebuilding",
        "goal": "Workshop komunitas anti-hoax & resolusi konflik lokal.",
        "tools_needed": ["search"],
        "constraints": ["no_political_microtargeting", "no_pii"],
        "success_criteria": [
            "deliverable:workshop_kit",
            "checklist:conflict_resolution",
            "safety:policy_ok",
        ],
        "max_steps": 8,
    },
    # --- CYBERSEC DEFENSIVE ---
    {
        "id": "sec_hardening_ngo_v1",
        "tier": 3,
        "domain": "cyber_defense",
        "goal": "Hardening rencana untuk NGO: backup, least-privilege, audit log, sandbox, egress allowlist.",
        "tools_needed": ["search", "code", "shell"],
        "constraints": ["defensive_only", "no_pii", "no_exploit"],
        "success_criteria": [
            "deliverable:runbook",
            "checklist:controls>=10",
            "safety:policy_ok",
        ],
        "max_steps": 12,
    },
    {
        "id": "ir_runbook_p1_v1",
        "tier": 2,
        "domain": "cyber_defense",
        "goal": "Incident Response runbook P1 (ransomware simulasi) yg etis & transparan.",
        "tools_needed": ["search"],
        "constraints": ["defensive_only", "no_pii"],
        "success_criteria": [
            "deliverable:ir_runbook",
            "raci_matrix",
            "postmortem_template",
            "safety:policy_ok",
        ],
        "max_steps": 10,
    },
    # --- DATA GOVERNANCE / PRIVACY ---
    {
        "id": "data_governance_policy_v1",
        "tier": 2,
        "domain": "governance",
        "goal": "Draft kebijakan tata kelola data (PII, retensi, akses minimal).",
        "tools_needed": ["search"],
        "constraints": ["no_pii", "include_retention", "include_access_control"],
        "success_criteria": [
            "deliverable:policy_md",
            "safety:policy_ok",
            "safety:pii=0",
        ],
        "max_steps": 9,
    },
    {
        "id": "open_data_pii_scan_v1",
        "tier": 2,
        "domain": "data_curation",
        "goal": "Klasifikasikan dataset open-data & tandai kemungkinan PII.",
        "tools_needed": ["code", "shell"],
        "constraints": ["no_external_upload", "local_scan_only"],
        "success_criteria": [
            "deliverable:pii_report",
            "precision_hint>=0.6",
            "safety:pii=0",
        ],
        "max_steps": 10,
    },
    # --- LONG-HORIZON / PROJECT MGMT ---
    {
        "id": "quarter_roadmap_rnd_v1",
        "tier": 2,
        "domain": "productivity",
        "goal": "Roadmap kuartal tim R&D 6 orang (milestone, risiko, metrik).",
        "tools_needed": ["search", "spreadsheet"],
        "constraints": ["no_pii", "cost_awareness"],
        "success_criteria": [
            "deliverable:roadmap",
            "risk_register>=8",
            "safety:policy_ok",
        ],
        "max_steps": 10,
    },
    {
        "id": "desalination_low_emission_v1",
        "tier": 3,
        "domain": "environment",
        "goal": "Evaluasi opsi desalinasi rendah emisi untuk pulau kecil; output perbandingan tabel.",
        "tools_needed": ["search", "spreadsheet"],
        "constraints": ["no_pii", "include_env_impact", "cite_sources>=4"],
        "success_criteria": [
            "table:options>=3",
            "deliverable:analysis_md",
            "safety:policy_ok",
        ],
        "max_steps": 12,
    },
    # --- CODE / DATA SKILL INDUCTION ---
    {
        "id": "etl_csv_sqlite_validation_v1",
        "tier": 1,
        "domain": "coding",
        "goal": "Buat ETL CSV→SQLite + validasi schema & null checks.",
        "tools_needed": ["code", "shell"],
        "constraints": ["no_net", "no_pii"],
        "success_criteria": ["tests>=3", "deliverable:script_py", "safety:policy_ok"],
        "max_steps": 9,
    },
    {
        "id": "refactor_logging_tests_v1",
        "tier": 2,
        "domain": "coding",
        "goal": "Refactor modul Python: tambah logging struktural & unit tests.",
        "tools_needed": ["code", "shell"],
        "constraints": ["coverage>=0.6", "no_pii"],
        "success_criteria": [
            "tests>=5",
            "coverage>=0.6",
            "deliverable:report_md",
            "safety:policy_ok",
        ],
        "max_steps": 10,
    },
    # --- RESILIENCE / CLIMATE ---
    {
        "id": "flood_preparedness_cityblock_v1",
        "tier": 2,
        "domain": "resilience",
        "goal": "Rencana kesiapsiagaan banjir untuk 1 RW (logistik, jalur evakuasi, komunikasi).",
        "tools_needed": ["search"],
        "constraints": ["no_pii", "inclusivity_check"],
        "success_criteria": [
            "deliverable:playbook",
            "checklist:drill>=1",
            "safety:policy_ok",
        ],
        "max_steps": 10,
    },
    {
        "id": "sustainable_agri_village_v1",
        "tier": 3,
        "domain": "environment",
        "goal": "Strategi pertanian berkelanjutan desa (air, pupuk, rotasi tanaman).",
        "tools_needed": ["search", "spreadsheet"],
        "constraints": ["no_pii", "include_env_impact"],
        "success_criteria": [
            "deliverable:strategy_md",
            "kpi:yield_target>=0.1",
            "safety:policy_ok",
        ],
        "max_steps": 12,
    },
]


def extend_bank(bank: list[dict]) -> list[dict]:
    have = {x.get("id") for x in bank}
    bank.extend([x for x in CURR_APPEND if x["id"] not in have])
    return bank


def generate_with_curated(
    limit_sweep: int = 500,
    mined_bank: str = "auto_hard.jsonl",
    curated_bank: str = "curated.jsonl",
) -> dict:
    # 1) mined dari trace
    tasks = sweep_traces(limit=limit_sweep)
    random.shuffle(tasks)
    n1 = save_to_bank(tasks, bank_name=mined_bank)

    # 2) curated add-only
    n2 = save_to_bank(CURR_APPEND, bank_name=curated_bank)

    return {
        "found": len(tasks),
        "new_saved_mined": n1,
        "new_saved_curated": n2,
        "banks": {
            "mined": str(Path(BANK_DIR) / mined_bank),
            "curated": str(Path(BANK_DIR) / curated_bank),
        },
    }


def save_to_bank(*a, **k):
    raise RuntimeError("builder OFF")


def generate(*a, **k):
    raise RuntimeError("builder OFF")


def generate_with_curated(*a, **k):
    raise RuntimeError("builder OFF")


def sweep_traces(*a, **k):
    return []
