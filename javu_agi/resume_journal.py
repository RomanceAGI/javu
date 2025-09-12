import os, json, time


def journal_path(base_dir: str, eid: str):
    d = os.path.join(base_dir, "journal")
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, f"{eid}.json")


def write_journal(path: str, data: dict):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)


def load_journal(path: str):
    try:
        return json.load(open(path, "r", encoding="utf-8"))
    except Exception:
        return None
