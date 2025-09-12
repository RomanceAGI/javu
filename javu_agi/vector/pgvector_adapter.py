from __future__ import annotations
from typing import List, Dict, Any, Tuple
import math, json, psycopg2

# NOTE: butuh ekstensi pgvector terpasang di DB target.


class PGVectorStore:
    """
    PGVector simple wrapper. Simpan vector (dim=256) + text + meta JSON.
    Pencarian pakai cosine <=> operator (pgvector >=0.5). Jika tidak ada, fallback L2.
    """

    def __init__(
        self, dsn: str, table: str = "vectors", dim: int = 256, use_cosine: bool = True
    ):
        self.dsn = dsn
        self.table = table
        self.dim = dim
        self.use_cosine = use_cosine
        self._ensure_table()

    def _conn(self):
        return psycopg2.connect(self.dsn)

    def _ensure_table(self):
        sql = f"""
        CREATE EXTENSION IF NOT EXISTS vector;
        CREATE TABLE IF NOT EXISTS {self.table} (
          id BIGSERIAL PRIMARY KEY,
          v vector({self.dim}) NOT NULL,
          text TEXT NOT NULL,
          meta JSONB
        );
        """
        with self._conn() as c, c.cursor() as cur:
            cur.execute(sql)

    def _embed(self, text: str) -> List[float]:
        dim = self.dim
        v = [0.0] * dim
        t = text.lower()
        for i in range(len(t) - 3):
            h = hash(t[i : i + 4]) % dim
            v[h] += 1.0
        n = math.sqrt(sum(x * x for x in v)) or 1.0
        return [x / n for x in v]

    def add(
        self,
        texts: List[str],
        metas: List[Dict[str, Any]] | None = None,
        collection: str = "default",
    ):
        metas = metas or [{} for _ in texts]
        sql = f"INSERT INTO {self.table} (v, text, meta) VALUES (%s, %s, %s)"
        with self._conn() as c, c.cursor() as cur:
            for txt, meta in zip(texts, metas):
                v = self._embed(txt[:4000])
                cur.execute(sql, (v, txt[:4000], json.dumps(meta)))

    def search(
        self, query: str, k: int = 8, collection: str = "default"
    ) -> List[Tuple[str, float, Dict[str, Any]]]:
        v = self._embed(query)
        with self._conn() as c, c.cursor() as cur:
            if self.use_cosine:
                sql = f"SELECT text, 1 - (v <=> %s) AS score, meta FROM {self.table} ORDER BY v <=> %s ASC LIMIT %s"
                cur.execute(sql, (v, v, k))
            else:
                sql = f"SELECT text, (1.0 - (v <-> %s)) AS score, meta FROM {self.table} ORDER BY v <-> %s ASC LIMIT %s"
                cur.execute(sql, (v, v, k))
            rows = cur.fetchall()
        out = []
        for text, score, meta in rows:
            out.append((text, float(score), meta or {}))
        return out
