import hashlib
import os
from javu_agi.utils.logger import log

ingested_files = {}  # {filename: hash}


def hash_file_content(content: str) -> str:
    return hashlib.sha256(content.encode()).hexdigest()


def ingest_file(file_path: str):
    if not os.path.exists(file_path):
        return False

    with open(file_path, "r") as f:
        content = f.read()

    h = hash_file_content(content)
    fname = os.path.basename(file_path)

    if fname in ingested_files and ingested_files[fname] == h:
        log(f"[FILE_INGEST] {fname} already ingested.")
        return False

    ingested_files[fname] = h
    log(f"[FILE_INGEST] New file: {fname}, size={len(content)}B")
    # You can extend here → store content to db/memory
    return True
