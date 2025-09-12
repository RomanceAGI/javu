import os, sqlite3, time, math
from typing import Optional

DB_PATH = os.getenv("SKILL_DB", os.path.join("data", "skills.db"))
SCHEMA = """
CREATE TABLE IF NOT EXISTS skills(
  name TEXT PRIMARY KEY,
  score REAL DEFAULT 1000.0,
  last_ts INTEGER
);
"""


class Competence:
    def __init__(self, db_path: str = DB_PATH):
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.db = sqlite3.connect(db_path, check_same_thread=False)
        with self.db:
            self.db.executescript(SCHEMA)

    def get(self, name: str) -> float:
        row = self.db.execute(
            "SELECT score FROM skills WHERE name=?", (name,)
        ).fetchone()
        return float(row[0]) if row else 1000.0

    def update(self, name: str, success: bool, latency_s: float, cost_usd: float):
        # ELO-like + penalty latency/cost
        k = 16.0
        score = self.get(name)
        outcome = 1.0 if success else 0.0
        penalty = 0.0 + 0.5 * math.log1p(max(0.0, latency_s)) + 2.0 * cost_usd
        new_score = max(300.0, score + k * (outcome - 0.5) - penalty)
        with self.db:
            self.db.execute(
                "INSERT INTO skills(name,score,last_ts) VALUES(?,?,?) "
                "ON CONFLICT(name) DO UPDATE SET score=excluded.score,last_ts=excluded.last_ts",
                (name, new_score, int(time.time())),
            )
        return new_score
