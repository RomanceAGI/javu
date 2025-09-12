from __future__ import annotations
import os, re, json, time, sqlite3, hashlib
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional, Callable

_DB = os.getenv("ROLE_SQLITE_PATH", "/data/roles.db")
_CANARY = os.getenv("ROLE_CANARY", "1") == "1"  # 1=butuh review manusia sebelum aktif
_AUTO_SAVE = os.getenv("ROLE_AUTO_SAVE", "1") == "1"  # 1=simpan hasil induksi ke store
_MAX_ROLES = int(os.getenv("ROLE_MAX", "2000"))


@dataclass
class RoleProfile:
    name: str
    goal_prefix: str
    allow_tools: List[str]
    deny_tools: List[str]
    tone: str
    policy_tags: List[str]
    approved: bool = False
    created_ts: float = 0.0
    hits: int = 0


# --- storage ---
_SCHEMA = """
PRAGMA journal_mode=WAL;
CREATE TABLE IF NOT EXISTS roles(
  name TEXT PRIMARY KEY,
  goal_prefix TEXT NOT NULL,
  allow_tools TEXT NOT NULL,
  deny_tools TEXT NOT NULL,
  tone TEXT NOT NULL,
  policy_tags TEXT NOT NULL,
  approved INTEGER NOT NULL,
  created_ts REAL NOT NULL,
  hits INTEGER NOT NULL
);
"""


def _conn():
    con = sqlite3.connect(_DB, timeout=3.0)
    con.execute("PRAGMA synchronous=NORMAL;")
    return con


def _init():
    con = _conn()
    for stmt in _SCHEMA.strip().split(";"):
        s = stmt.strip()
        if s:
            con.execute(s)
    con.commit()
    con.close()


def _row_to_role(r) -> RoleProfile:
    return RoleProfile(
        name=r[0],
        goal_prefix=r[1],
        allow_tools=json.loads(r[2]),
        deny_tools=json.loads(r[3]),
        tone=r[4],
        policy_tags=json.loads(r[5]),
        approved=bool(r[6]),
        created_ts=float(r[7]),
        hits=int(r[8]),
    )


# --- heuristics: open-world extraction tanpa LLM (deterministik & ToS-safe) ---
_TAGS = {
    "edu": ["teach", "guru", "kurikulum", "lesson", "student", "education"],
    "gov": ["policy", "kebijakan", "regulation", "govern", "perda", "permen", "public"],
    "swe": [
        "software",
        "engineer",
        "service",
        "api",
        "app",
        "game",
        "deploy",
        "infra",
        "devops",
    ],
    "sci": ["riset", "research", "experiment", "hypothesis", "paper", "dataset", "lab"],
    "biz": [
        "market",
        "sales",
        "growth",
        "budget",
        "finance",
        "accounting",
        "ops",
        "legal",
    ],
    "design": [
        "ui",
        "ux",
        "mockup",
        "wireframe",
        "brand",
        "identity",
        "visual",
        "asset",
    ],
}

_DEFAULT_TONE = "professional, concise"
_TOOL_SETS = {
    "edu": ["gdrive", "gcal", "gmail"],
    "gov": ["web", "notion"],
    "swe": ["web", "github", "gdrive", "slack"],
    "sci": ["web", "gdrive", "notion"],
    "biz": ["web", "gdrive", "slack"],
    "design": ["web", "gdrive"],
}


def _hash_name(s: str) -> str:
    # deterministik: role-<hash-8>
    h = hashlib.sha256(s.encode("utf-8")).hexdigest()[:8]
    return f"role-{h}"


def _infer_tags(task: str) -> List[str]:
    t = task.lower()
    tags = []
    for k, kws in _TAGS.items():
        if any(w in t for w in kws):
            tags.append(k)
    return tags or ["biz"]  # default general-purpose


def _make_profile_from_task(task: str) -> RoleProfile:
    tags = _infer_tags(task)
    # nama role dari noun-phrase sederhana + hash → open-world
    words = re.findall(r"[a-zA-Z]{4,}", task.lower())
    head = "-".join(words[:3]) if words else "generalist"
    name = _hash_name(head + "|" + ",".join(tags))
    allow = sorted(list({t for tag in tags for t in _TOOL_SETS.get(tag, [])}))
    deny = []  # bisa diisi dari policy nanti
    goal = "Operate as a capable {} across tasks: {}".format(
        ", ".join(tags), head.replace("-", " ")
    )
    return RoleProfile(
        name=name,
        goal_prefix=goal,
        allow_tools=allow,
        deny_tools=deny,
        tone=_DEFAULT_TONE,
        policy_tags=tags,
        approved=(not _CANARY),
        created_ts=time.time(),
        hits=0,
    )


class DynamicIdentityManager:
    """
    Open-world role system:
    - Lookup role yang sudah ada (by semantic fingerprint)
    - Jika belum ada → induce dari task (deterministik), optional human review (canary)
    - Persist ke store agar reusable lintas sesi
    - Tidak bergantung daftar role statis
    """

    def __init__(
        self, synth_fn: Optional[Callable[[str], Optional[RoleProfile]]] = None
    ):
        _init()
        self.synth_fn = synth_fn  # opsional: gunakan LLM untuk deskripsi lebih kaya (tetap lewat guard)

    def _get(self, name: str) -> Optional[RoleProfile]:
        con = _conn()
        cur = con.execute("SELECT * FROM roles WHERE name=?", (name,))
        row = cur.fetchone()
        con.close()
        return _row_to_role(row) if row else None

    def _upsert(self, rp: RoleProfile):
        con = _conn()
        con.execute(
            "INSERT INTO roles(name,goal_prefix,allow_tools,deny_tools,tone,policy_tags,approved,created_ts,hits) "
            "VALUES(?,?,?,?,?,?,?,?,?) "
            "ON CONFLICT(name) DO UPDATE SET goal_prefix=excluded.goal_prefix, "
            "allow_tools=excluded.allow_tools, deny_tools=excluded.deny_tools, "
            "tone=excluded.tone, policy_tags=excluded.policy_tags",
            (
                rp.name,
                rp.goal_prefix,
                json.dumps(rp.allow_tools),
                json.dumps(rp.deny_tools),
                rp.tone,
                json.dumps(rp.policy_tags),
                int(rp.approved),
                rp.created_ts,
                rp.hits,
            ),
        )
        con.commit()
        con.close()

    def _bump(self, name: str):
        con = _conn()
        con.execute("UPDATE roles SET hits = hits + 1 WHERE name=?", (name,))
        con.commit()
        con.close()

    def infer_role(self, task_text: str) -> RoleProfile:
        # 1) fingerprint → cari role existing
        fp = _hash_name(task_text.lower())
        rp = self._get(fp)
        if rp:
            self._bump(rp.name)
            return rp

        # 2) bikin role baru (deterministik, tanpa LLM)
        rp = _make_profile_from_task(task_text)
        rp.name = (
            fp  # gunakan fingerprint sebagai id role (open-world, unik per intent)
        )
        # 3) optional synth (LLM) → perindah goal_prefix/allow_tools (tetap guarded)
        if self.synth_fn:
            try:
                alt = self.synth_fn(task_text)
                if isinstance(alt, RoleProfile):
                    # merge ringan; tetap enforce allow/deny whitelist
                    if alt.goal_prefix:
                        rp.goal_prefix = alt.goal_prefix[:400]
                    if alt.tone:
                        rp.tone = alt.tone[:120]
            except Exception:
                pass
        # 4) persist (kalau quota role tidak melebihi batas)
        if _AUTO_SAVE:
            con = _conn()
            cur = con.execute("SELECT COUNT(1) FROM roles")
            n = int(cur.fetchone()[0])
            con.close()
            if n < _MAX_ROLES:
                self._upsert(rp)
        return rp

    def approve(self, name: str):
        con = _conn()
        con.execute("UPDATE roles SET approved=1 WHERE name=?", (name,))
        con.commit()
        con.close()

    def list_roles(self, limit: int = 50) -> List[RoleProfile]:
        con = _conn()
        cur = con.execute(
            "SELECT * FROM roles ORDER BY created_ts DESC LIMIT ?", (int(limit),)
        )
        rows = [_row_to_role(r) for r in cur.fetchall()]
        con.close()
        return rows
