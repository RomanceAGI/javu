from __future__ import annotations
import os, sqlite3, json, time
from typing import List, Dict, Optional, Tuple

_DB = os.getenv("KB_SQLITE_PATH", "/data/kb.db")

_SCHEMA = """
PRAGMA journal_mode=WAL;
CREATE TABLE IF NOT EXISTS kb_docs(
  doc_id TEXT PRIMARY KEY,
  meta_json TEXT NOT NULL,
  ts REAL NOT NULL
);
CREATE VIRTUAL TABLE IF NOT EXISTS kb_chunks USING fts5(
  doc_id, chunk, tokenize="porter"
);
"""


def _conn():
    con = sqlite3.connect(_DB, timeout=3.0)
    con.execute("PRAGMA synchronous=NORMAL;")
    return con


def init():
    con = _conn()
    for stmt in _SCHEMA.strip().split(";"):
        s = stmt.strip()
        if s:
            con.execute(s)
    con.commit()
    con.close()


def upsert_doc(doc_id: str, text: str, meta: Dict):
    init()
    # naive chunking
    chunks = []
    step = 800
    for i in range(0, len(text), step):
        chunks.append(text[i : i + step])
    con = _conn()
    con.execute(
        "INSERT INTO kb_docs(doc_id, meta_json, ts) VALUES(?,?,?) ON CONFLICT(doc_id) DO UPDATE SET meta_json=excluded.meta_json, ts=excluded.ts",
        (doc_id, json.dumps(meta), time.time()),
    )
    con.execute("DELETE FROM kb_chunks WHERE doc_id=?", (doc_id,))
    con.executemany(
        "INSERT INTO kb_chunks(doc_id, chunk) VALUES(?,?)",
        [(doc_id, c) for c in chunks],
    )
    con.commit()
    con.close()


def search(query: str, k: int = 6) -> List[Tuple[str, str]]:
    init()
    con = _conn()
    cur = con.execute(
        "SELECT doc_id, snippet(kb_chunks, 1, '[', ']', ' ... ', 6) FROM kb_chunks WHERE kb_chunks MATCH ? LIMIT ?",
        (query, int(k)),
    )
    rows = [(r[0], r[1]) for r in cur.fetchall()]
    con.close()
    return rows


def retrieve_context(query: str, k: int = 6) -> str:
    hits = search(query, k)
    # join snippet; planner can insert this as context
    return "\n".join(f"[{did}] {snip}" for did, snip in hits)
