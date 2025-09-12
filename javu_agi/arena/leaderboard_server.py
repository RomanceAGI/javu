from fastapi import FastAPI
import sqlite3, os

app = FastAPI(title="Arena Leaderboard")
DB = os.getenv("ARENA_DB", "arena/arena.db")


@app.get("/leaderboard/daily")
def daily():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    rows = cur.execute(
        "SELECT ts,arena,transfer,adversarial,soak,human FROM daily_metrics ORDER BY ts DESC LIMIT 30"
    ).fetchall()
    return [
        {
            "ts": r[0],
            "arena": r[1],
            "transfer": r[2],
            "adversarial": r[3],
            "soak": r[4],
            "human": r[5],
        }
        for r in rows
    ]
