import os, sqlite3, time, json, math, struct
from typing import List, Dict, Any, Optional
import numpy as np

DATA_DIR = os.getenv("DATA_DIR", "data")
DB_PATH = os.getenv("MEMORY_DB", os.path.join(DATA_DIR, "memory.db"))
EMB_DIM = int(os.getenv("EMBED_DIM", "1536"))

SCHEMA = """
PRAGMA journal_mode=WAL;
CREATE TABLE IF NOT EXISTS episodic(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ts INTEGER, user TEXT, task TEXT,
  text TEXT, meta TEXT
);
CREATE TABLE IF NOT EXISTS semantic(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ts INTEGER, subj TEXT, pred TEXT, obj TEXT, conf REAL, source_ep INTEGER
);
CREATE TABLE IF NOT EXISTS vectors(
  id INTEGER PRIMARY KEY,
  kind TEXT,               -- 'episodic' | 'doc'
  dim INTEGER,
  vec  BLOB                -- float32[dim]
);
CREATE INDEX IF NOT EXISTS idx_ep_ts ON episodic(ts);
CREATE INDEX IF NOT EXISTS idx_sem ON semantic(subj, pred, obj);
CREATE INDEX IF NOT EXISTS idx_vec_kind ON vectors(kind);
"""


def _pack(v: np.ndarray) -> bytes:
    v = v.astype(np.float32, copy=False).ravel()
    return struct.pack(f"{len(v)}f", *v.tolist())


def _unpack(b: bytes) -> np.ndarray:
    n = len(b) // 4
    return np.array(struct.unpack(f"{n}f", b), dtype=np.float32)


def _cos(a: np.ndarray, b: np.ndarray) -> float:
    na = np.linalg.norm(a) + 1e-9
    nb = np.linalg.norm(b) + 1e-9
    return float(np.dot(a, b) / (na * nb))


class MemoryDB:
    def __init__(self, path: str = DB_PATH):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        self.db = sqlite3.connect(path, check_same_thread=False)
        with self.db:
            self.db.executescript(SCHEMA)

    # ---- episodic ----
    def add_episode(self, user: str, task: str, text: str, meta: Dict[str, Any]) -> int:
        ts = int(time.time())
        with self.db:
            cur = self.db.execute(
                "INSERT INTO episodic(ts,user,task,text,meta) VALUES(?,?,?,?,?)",
                (ts, user, task, text, json.dumps(meta, ensure_ascii=False)),
            )
        return int(cur.lastrowid)

    def add_vector(self, row_id: int, kind: str, emb: np.ndarray):
        with self.db:
            self.db.execute(
                "INSERT OR REPLACE INTO vectors(id,kind,dim,vec) VALUES(?,?,?,?)",
                (row_id, kind, len(emb), _pack(emb)),
            )

    def recent_episodes(self, limit: int = 20) -> List[Dict[str, Any]]:
        q = "SELECT id,ts,user,task,text,meta FROM episodic ORDER BY id DESC LIMIT ?"
        rows = self.db.execute(q, (limit,)).fetchall()
        out = []
        for r in rows:
            out.append(
                {
                    "id": r[0],
                    "ts": r[1],
                    "user": r[2],
                    "task": r[3],
                    "text": r[4],
                    "meta": json.loads(r[5] or "{}"),
                }
            )
        return out

    # ---- semantic ----
    def add_fact(
        self,
        subj: str,
        pred: str,
        obj: str,
        conf: float,
        source_ep: Optional[int] = None,
    ):
        ts = int(time.time())
        with self.db:
            self.db.execute(
                "INSERT INTO semantic(ts,subj,pred,obj,conf,source_ep) VALUES(?,?,?,?,?,?)",
                (ts, subj, pred, obj, float(conf), source_ep),
            )

    def query_facts(
        self,
        subj: Optional[str] = None,
        pred: Optional[str] = None,
        obj: Optional[str] = None,
        limit=50,
    ):
        q = "SELECT ts,subj,pred,obj,conf,source_ep FROM semantic WHERE 1=1"
        args = []
        if subj:
            q += " AND subj=?"
            args.append(subj)
        if pred:
            q += " AND pred=?"
            args.append(pred)
        if obj:
            q += " AND obj=?"
            args.append(obj)
        q += " ORDER BY ts DESC LIMIT ?"
        args.append(limit)
        return [
            dict(zip(["ts", "subj", "pred", "obj", "conf", "source_ep"], r))
            for r in self.db.execute(q, tuple(args)).fetchall()
        ]

    # ---- vector recall ----
    def recall(
        self, qvec: np.ndarray, kind: str = "episodic", k: int = 5
    ) -> List[Dict[str, Any]]:
        rows = self.db.execute(
            "SELECT id,dim,vec FROM vectors WHERE kind=?", (kind,)
        ).fetchall()
        scored = []
        for rid, dim, vecb in rows:
            v = _unpack(vecb)
            if v.shape[0] != qvec.shape[0]:
                continue
            scored.append((rid, _cos(qvec, v)))
        scored.sort(key=lambda x: x[1], reverse=True)
        ids = [rid for rid, _ in scored[:k]]
        if not ids:
            return []
        q = f"SELECT id,ts,user,task,text,meta FROM episodic WHERE id IN ({','.join('?'*len(ids))})"
        out = []
        for r in self.db.execute(q, tuple(ids)).fetchall():
            out.append(
                {
                    "id": r[0],
                    "ts": r[1],
                    "user": r[2],
                    "task": r[3],
                    "text": r[4],
                    "meta": json.loads(r[5] or "{}"),
                }
            )
        return out
