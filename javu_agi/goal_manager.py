import os, sqlite3, time
from typing import List, Optional, Dict, Any, Tuple

DB_PATH = os.getenv("GOALS_DB", os.path.join("data", "goals.db"))

SCHEMA = """
CREATE TABLE IF NOT EXISTS goals(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  parent_id INTEGER,
  title TEXT NOT NULL,
  detail TEXT,
  priority INTEGER DEFAULT 0,
  status TEXT DEFAULT 'todo', -- todo|doing|done|blocked
  created_at INTEGER, updated_at INTEGER, due_ts INTEGER,
  UNIQUE(title, COALESCE(parent_id, -1))
);
CREATE INDEX IF NOT EXISTS idx_goals_status ON goals(status);
CREATE INDEX IF NOT EXISTS idx_goals_parent ON goals(parent_id);
"""


class GoalManager:
    def __init__(self, db_path: str = DB_PATH):
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.db = sqlite3.connect(db_path, check_same_thread=False)
        with self.db:
            self.db.executescript(SCHEMA)

    def add(
        self,
        title: str,
        detail: str = "",
        priority: int = 0,
        parent_id: Optional[int] = None,
        due_ts: Optional[int] = None,
    ) -> int:
        now = int(time.time())
        with self.db:
            cur = self.db.execute(
                "INSERT OR IGNORE INTO goals(parent_id,title,detail,priority,status,created_at,updated_at,due_ts)"
                " VALUES(?,?,?,?, 'todo', ?, ?, ?)",
                (parent_id, title, detail, priority, now, now, due_ts),
            )
        return cur.lastrowid or self.get_id(title, parent_id)

    def get_id(self, title: str, parent_id: Optional[int]) -> Optional[int]:
        row = self.db.execute(
            "SELECT id FROM goals WHERE title=? AND COALESCE(parent_id,-1)=COALESCE(?, -1)",
            (title, parent_id),
        ).fetchone()
        return row[0] if row else None

    def update_status(self, goal_id: int, status: str):
        with self.db:
            self.db.execute(
                "UPDATE goals SET status=?, updated_at=? WHERE id=?",
                (status, int(time.time()), goal_id),
            )

    def next_batch(self, k: int = 5) -> List[Dict[str, Any]]:
        q = (
            "SELECT id,parent_id,title,detail,priority,due_ts FROM goals "
            "WHERE status IN ('todo','doing') ORDER BY priority DESC, COALESCE(due_ts, 1e18) ASC, id ASC LIMIT ?"
        )
        rows = self.db.execute(q, (k,)).fetchall()
        return [
            {
                "id": r[0],
                "parent_id": r[1],
                "title": r[2],
                "detail": r[3],
                "priority": r[4],
                "due_ts": r[5],
            }
            for r in rows
        ]

    def subgoals(self, parent_id: int) -> List[Dict[str, Any]]:
        rows = self.db.execute(
            "SELECT id,title,status FROM goals WHERE parent_id=? ORDER BY id",
            (parent_id,),
        ).fetchall()
        return [{"id": r[0], "title": r[1], "status": r[2]} for r in rows]

    def list_active(self):
        return [g for g in getattr(self, "goals", []) if not g.get("done")]

    def report(self, gid: str, success: bool):
        for g in getattr(self, "goals", []):
            if g.get("id") == gid:
                g["done"] = bool(success)
                return
