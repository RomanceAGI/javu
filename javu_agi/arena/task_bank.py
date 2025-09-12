from __future__ import annotations
import os, json, time, hashlib, random, glob
import time, uuid
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

# === Paths ==================================================
DATA_DIR = Path(os.getenv("DATA_DIR", "./data")).resolve()
BANKS_DIR = DATA_DIR / "banks"
RUNTIME_DIR = Path(os.getenv("RUNTIME_DIR", str(DATA_DIR / "runtime")))

for d in (DATA_DIR, BANKS_DIR, RUNTIME_DIR):
    d.mkdir(parents=True, exist_ok=True)


# === JSONL Utils ===========================================
def _hash_record(rec: Dict[str, Any]) -> str:
    # Hash hanya field penting supaya dedup konsisten
    key = json.dumps(
        {
            "task": rec.get("task", "").strip(),
            "category": rec.get("category", ""),
            "difficulty": rec.get("difficulty", ""),
        },
        sort_keys=True,
        ensure_ascii=False,
    )
    return hashlib.sha256(key.encode("utf-8")).hexdigest()


def load_bank(name_or_path: str | Path) -> List[Dict[str, Any]]:
    """Load JSONL bank. name bisa 'auto_easy.jsonl' atau full path."""
    p = Path(name_or_path)
    if not p.suffix:
        p = BANKS_DIR / f"{p.name}.jsonl"
    if not p.is_file():
        return []
    out: List[Dict[str, Any]] = []
    with p.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                if isinstance(obj, dict) and "task" in obj:
                    out.append(obj)
            except Exception:
                # skip corrupt lines, do not fail loop
                continue
    return out


def save_to_bank(
    records: Iterable[Dict[str, Any]], bank_name: str, dedup: bool = True
) -> Tuple[int, int]:
    """
    Append records to banks/<bank_name> (JSONL).
    Returns: (written, skipped)
    """
    path = BANKS_DIR / bank_name
    path.parent.mkdir(parents=True, exist_ok=True)

    existing = {}
    if path.exists() and dedup:
        for r in load_bank(path):
            existing[_hash_record(r)] = True

    written = 0
    skipped = 0
    with path.open("a", encoding="utf-8") as f:
        for rec in records:
            if not isinstance(rec, dict) or "task" not in rec:
                skipped += 1
                continue
            rec.setdefault("category", "general")
            rec.setdefault("difficulty", "medium")
            h = _hash_record(rec)
            if dedup and h in existing:
                skipped += 1
                continue
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            if dedup:
                existing[h] = True
            written += 1
    return written, skipped


# === SCHEMA HARDENING (PRO) =================================
SCHEMA_VERSION = 1
_ALLOWED_DIFF = {"easy", "medium", "hard"}


def _normalize_diff(x: str) -> str:
    x = str(x or "medium").lower().strip()
    return x if x in _ALLOWED_DIFF else "medium"


def enforce_schema(records):
    """
    Pastikan tiap record punya: task, category, difficulty, id, source, added_at, version.
    """
    out = []
    now = int(time.time())
    for r in records or []:
        if not isinstance(r, dict):
            continue
        t = (r.get("task") or "").strip()
        if not t:
            continue
        r = dict(r)
        r["category"] = (r.get("category") or "general").strip()
        r["difficulty"] = _normalize_diff(r.get("difficulty") or "medium")
        r["version"] = r.get("version", SCHEMA_VERSION)
        r["added_at"] = int(r.get("added_at", now))
        r["source"] = (r.get("source") or "manual").strip()
        # ID deterministik berdasar isi utama
        r["id"] = r.get("id") or str(
            uuid.uuid5(uuid.NAMESPACE_URL, f"{t}|{r['category']}|{r['difficulty']}")
        )
        out.append(r)
    return out


# === override save_to_bank agar pakai enforce_schema + dedup ===
_old_save_to_bank = save_to_bank  # gunakan yang sudah ada


def save_to_bank(records, bank_name: str, dedup: bool = True):
    return _old_save_to_bank(enforce_schema(records), bank_name, dedup=dedup)


# === LINT & COUNT ===========================================
def lint_banks(patterns=None):
    import glob

    patterns = patterns or DEFAULT_PATTERNS
    seen = set()
    total = {"easy": 0, "medium": 0, "hard": 0}
    bad = 0
    files = set()
    for pat in patterns:
        for fp in glob.glob(pat):
            files.add(fp)
            for r in load_bank(fp):
                try:
                    r = enforce_schema([r])[0]
                except Exception:
                    bad += 1
                    continue
                h = _hash_record(r)
                if h in seen:
                    continue
                seen.add(h)
                total[r["difficulty"]] += 1
    return {
        "files": sorted(files),
        "total": total,
        "bad": bad,
        "grand_total": sum(total.values()),
    }


def print_lint_report():
    rep = lint_banks()
    print("[lint] files:", *rep["files"], sep="\n  - ")
    print(
        f"[lint] totals: easy={rep['total']['easy']}, medium={rep['total']['medium']}, "
        f"hard={rep['total']['hard']}, grand_total={rep['grand_total']}, bad_lines={rep['bad']}"
    )


# === MIGRATOR (sekali jalan) ================================
def migrate_all_banks(patterns=None, dry_run=False):
    import glob

    patterns = patterns or DEFAULT_PATTERNS
    changed = 0
    for pat in patterns:
        for fp in glob.glob(pat):
            recs = load_bank(fp)
            if not recs:
                continue
            fixed = enforce_schema(recs)
            if dry_run:
                print(f"[migrate] would update {fp}: {len(recs)} → {len(fixed)}")
                continue
            # rewrite atomic
            tmp = Path(fp).with_suffix(".jsonl.tmp")
            with tmp.open("w", encoding="utf-8") as f:
                for r in fixed:
                    f.write(json.dumps(r, ensure_ascii=False) + "\n")
            tmp.replace(fp)
            print(f"[migrate] updated {fp}: {len(recs)} → {len(fixed)}")
            changed += 1
    return changed


# === Sampler ================================================
DEFAULT_PATTERNS = [
    str(BANKS_DIR / "auto_*.jsonl"),
    str(BANKS_DIR / "extra_*.jsonl"),
    str(BANKS_DIR / "*_heavy.jsonl"),
    str(BANKS_DIR / "transfer_test*.jsonl"),
    str(BANKS_DIR / "extra_transfer.jsonl"),
    str(BANKS_DIR / "adversarial_redteam.jsonl"),
    str(BANKS_DIR / "high_impact.jsonl"),
    str(BANKS_DIR / "vision_rag.jsonl"),
]


def sample_all_banks(
    patterns: List[str] | None = None,
    mix_ratio: Dict[str, float] | None = None,
    total: int = 100,
    shuffle_seed: int | None = None,
) -> List[Dict[str, Any]]:
    """
    Baca semua bank yang match pola dan sampling seimbang (default 70/20/10).
    Difficulty yg didukung: easy / medium / hard (default -> medium).
    """
    patterns = patterns or DEFAULT_PATTERNS
    mix_ratio = mix_ratio or {"easy": 0.7, "medium": 0.2, "hard": 0.1}

    pools: Dict[str, List[Dict[str, Any]]] = {"easy": [], "medium": [], "hard": []}
    for pat in patterns:
        for fp in glob.glob(pat):
            for rec in load_bank(fp):
                diff = str(rec.get("difficulty", "medium")).lower()
                if diff not in pools:
                    diff = "medium"
                pools[diff].append(rec)

    # alokasi per difficulty
    alloc = {k: max(0, int(total * w)) for k, w in mix_ratio.items()}
    # koreksi rounding
    remain = total - sum(alloc.values())
    if remain > 0:
        alloc["hard"] = alloc.get("hard", 0) + remain

    rng = random.Random(shuffle_seed)
    out: List[Dict[str, Any]] = []
    for diff, k in alloc.items():
        pool = pools[diff]
        if not pool:
            continue
        rng.shuffle(pool)
        out.extend(pool[:k])

    rng.shuffle(out)
    return out


# === Injector Hard-Cases ====================================
def append_hard_cases(hard_cases: List[Dict[str, Any]]) -> Tuple[int, int]:
    """
    Tambah hard-cases (misal dari kegagalan/hard failures harian) ke auto_hard.jsonl.
    Auto-set difficulty='hard' jika belum ada.
    """
    payload = []
    for hc in hard_cases or []:
        if not isinstance(hc, dict) or "task" not in hc:
            continue
        hc = dict(hc)
        hc.setdefault("category", "unknown")
        hc["difficulty"] = "hard"
        payload.append(hc)
    return save_to_bank(payload, "auto_hard.jsonl")


# === FINAL HIGH-IMPACT BATCH ================================
# Kumpulan tugas berdampak tinggi untuk mempercepat generalisasi & meta-learning.
HIGH_IMPACT: List[Dict[str, Any]] = [
    # Robotics & Control
    {
        "task": "Simulate robotic arm pick-and-place using PyBullet",
        "category": "robotics",
        "difficulty": "hard",
    },
    {
        "task": "Autonomous drone navigation indoor/outdoor dengan batas keselamatan",
        "category": "robotics",
        "difficulty": "hard",
    },
    {
        "task": "Path planning + obstacle avoidance untuk robot mobile (grid & continuous)",
        "category": "robotics",
        "difficulty": "hard",
    },
    {
        "task": "Vision-based grasp recognition dari kamera RGB",
        "category": "robotics",
        "difficulty": "hard",
    },
    {
        "task": "Real-time SLAM di lingkungan tak dikenal",
        "category": "robotics",
        "difficulty": "hard",
    },
    # Scientific & Engineering
    {
        "task": "Formulasikan & uji hipotesis ilmiah dari kumpulan observasi terbatas",
        "category": "science",
        "difficulty": "hard",
    },
    {
        "task": "Analisis genom & prediksi struktur protein (konsep + evaluasi)",
        "category": "bio",
        "difficulty": "hard",
    },
    {
        "task": "Pemodelan fluida/partikel untuk eksperimen engineering kecil",
        "category": "science",
        "difficulty": "hard",
    },
    {
        "task": "Optimasi tata letak panel surya untuk efisiensi harian",
        "category": "energy",
        "difficulty": "hard",
    },
    {
        "task": "Desain bilah turbin angin via pertimbangan CFD (konsep)",
        "category": "energy",
        "difficulty": "hard",
    },
    # High-Stakes Reasoning
    {
        "task": "Optimasi rute logistik skala besar multi-kendala",
        "category": "operations",
        "difficulty": "hard",
    },
    {
        "task": "Risk assessment rantai pasok global + mitigasi",
        "category": "operations",
        "difficulty": "hard",
    },
    {
        "task": "Simulasi pengambilan keputusan saat krisis (trade-off & etika)",
        "category": "reasoning",
        "difficulty": "hard",
    },
    {
        "task": "Negotiation AI untuk perjanjian/kontrak (strategi & BATNA)",
        "category": "reasoning",
        "difficulty": "hard",
    },
    {
        "task": "Perencanaan portofolio skenario multi-pasar (bukan trading live)",
        "category": "finance",
        "difficulty": "hard",
    },
    # Meta-Learning & Self-Improvement
    {
        "task": "Self-debug reasoning chain (deteksi kontradiksi & missing steps)",
        "category": "meta",
        "difficulty": "hard",
    },
    {
        "task": "Self-rewrite algoritma internal untuk efisiensi latensi/biaya",
        "category": "meta",
        "difficulty": "hard",
    },
    {
        "task": "Auto-curriculum dari kelemahan historis (EMA win-rate)",
        "category": "meta",
        "difficulty": "hard",
    },
    {
        "task": "Hyperparameter auto-tuning untuk router & planner",
        "category": "meta",
        "difficulty": "hard",
    },
    {
        "task": "Cross-agent knowledge sharing (distill ringkas)",
        "category": "meta",
        "difficulty": "hard",
    },
    # Perception & Multimodal
    {
        "task": "Multimodal reasoning: gabungkan teks+gambar+audio+sensor ke 1 loop",
        "category": "multimodal",
        "difficulty": "hard",
    },
    {
        "task": "Speech-to-speech translation real-time dengan fallback aman",
        "category": "multimodal",
        "difficulty": "hard",
    },
    {
        "task": "Video event detection & action recognition dari klip pendek",
        "category": "multimodal",
        "difficulty": "hard",
    },
    {
        "task": "OCR dokumen kompleks + verifikasi kutipan (citations)",
        "category": "vision",
        "difficulty": "hard",
    },
    {
        "task": "Cross-modal retrieval (query teks→gambar→audio)",
        "category": "multimodal",
        "difficulty": "hard",
    },
    # Extreme Generalization & Transfer
    {
        "task": "Zero-shot reasoning untuk tugas baru tanpa contoh",
        "category": "transfer",
        "difficulty": "hard",
    },
    {
        "task": "Sim2Real: adaptasi dari simulasi ke dunia nyata (prosedur)",
        "category": "transfer",
        "difficulty": "hard",
    },
    {
        "task": "Few-shot learning dengan data minimal (k<5)",
        "category": "transfer",
        "difficulty": "hard",
    },
    {
        "task": "Memecahkan puzzle baru tanpa pernah melihat contoh",
        "category": "transfer",
        "difficulty": "hard",
    },
    {
        "task": "Multi-domain reasoning chain lintas format data",
        "category": "transfer",
        "difficulty": "hard",
    },
    # Ethics & Alignment
    {
        "task": "Analisis dilema moral & trade-off; jelaskan keputusan final",
        "category": "ethics",
        "difficulty": "hard",
    },
    {
        "task": "Prediksi dampak jangka panjang dari suatu keputusan",
        "category": "ethics",
        "difficulty": "hard",
    },
    {
        "task": "Deteksi & mitigasi bias pada reasoning",
        "category": "ethics",
        "difficulty": "hard",
    },
    {
        "task": "Penjelasan transparan (XAI) untuk keputusan sulit",
        "category": "ethics",
        "difficulty": "hard",
    },
    {
        "task": "Value alignment dengan tujuan pengguna & kebijakan",
        "category": "ethics",
        "difficulty": "hard",
    },
]

# Persist sekali (idempotent & dedup)
_written, _skipped = save_to_bank(HIGH_IMPACT, "high_impact.jsonl", dedup=True)


# === Helper: buat batch =====================================
def build_training_batch(
    total: int = 500,
    mix_ratio: Dict[str, float] | None = None,
    shuffle_seed: int | None = None,
) -> List[Dict[str, Any]]:
    """Paket siap kirim ke core loop/arena."""
    batch = sample_all_banks(
        mix_ratio=mix_ratio, total=total, shuffle_seed=shuffle_seed
    )
    # Optionally injeksi sebagian hard-cases terbaru (tergantung sistem lo)
    return batch


def export_batch_for_eval(total=200, seed=None, out="data/runtime/eval_batch.jsonl"):
    batch = build_training_batch(total=total, shuffle_seed=seed)
    with open(out, "w", encoding="utf-8") as f:
        for r in batch:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    return out


# === CLI kecil ==============================================
def _cli():
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--total", type=int, default=100, help="jumlah sample")
    ap.add_argument("--seed", type=int, default=None, help="shuffle seed")
    ap.add_argument("--dump", type=str, default="", help="tulis batch ke path (.jsonl)")
    args = ap.parse_args()

    batch = build_training_batch(total=args.total, shuffle_seed=args.seed)
    print(f"[task_bank] loaded high_impact: +{_written} (skipped { _skipped })")
    print(f"[task_bank] sample batch: {len(batch)} items")
    if args.dump:
        out = Path(args.dump)
        out.parent.mkdir(parents=True, exist_ok=True)
        with out.open("w", encoding="utf-8") as f:
            for r in batch:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        print(f"[task_bank] dumped -> {out}")


if __name__ == "__main__":
    _cli()


def save_to_bank(*a, **k):
    return (0, 0)


def inject_hard_cases(*a, **k):
    return (0, 0)


def inject_high_impact(*a, **k):
    return (0, 0)


_written, _skipped = 0, 0
