import time, json, os, sqlite3, glob
from pathlib import Path

DB = "arena/arena.db"
os.makedirs("arena", exist_ok=True)
conn = sqlite3.connect(DB)
cur = conn.cursor()
cur.execute(
    """CREATE TABLE IF NOT EXISTS daily_metrics(
  ts INTEGER PRIMARY KEY, arena REAL, transfer REAL, adversarial REAL, soak REAL, human REAL
)"""
)
conn.commit()


def upsert_from_json(path):
    with open(path) as f:
        data = json.load(f)
    ts = int(Path(path).stat().st_mtime)
    cur.execute(
        "INSERT OR REPLACE INTO daily_metrics(ts,arena,transfer,adversarial,soak,human) VALUES(?,?,?,?,?,?)",
        (
            ts,
            data.get("arena"),
            data.get("transfer"),
            data.get("adversarial"),
            data.get("soak"),
            data.get("human"),
        ),
    )
    conn.commit()


def main(watch_dir):
    last_seen = set()
    while True:
        files = glob.glob(os.path.join(watch_dir, "*.json"))
        for p in files:
            if p not in last_seen:
                upsert_from_json(p)
                last_seen.add(p)
        time.sleep(10)


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--watch_dir", default="arena_logs/daily")
    args = ap.parse_args()
    main(args.watch_dir)
