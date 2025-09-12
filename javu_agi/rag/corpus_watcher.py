from __future__ import annotations
import time, json, hashlib
from pathlib import Path
from typing import Dict, List, Callable
from javu_agi.rag.ingest import ingest_texts
from javu_agi.rag.parsers import read_text_file, read_md_file, read_log_file

READERS: Dict[str, Callable[[Path], str]] = {
    ".txt": read_text_file,
    ".md": read_md_file,
    ".log": read_log_file,
}


def _fingerprint(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", "ignore")).hexdigest()


class CorpusWatcher:
    """
    Scan folder korpus → deteksi file baru/berubah → ingest ke vector store.
    Simpel, no dep berat; cocok buat VPS kecil.
    """

    def __init__(
        self,
        folder: str = "data/corpus",
        state_path: str = "data/corpus_state.json",
        collection: str = "agi_facts",
        interval_s: int = 60,
        chunk_limit: int = 8000,
    ):
        self.folder = Path(folder)
        self.state_path = Path(state_path)
        self.collection = collection
        self.interval_s = interval_s
        self.chunk_limit = chunk_limit
        self.state = self._load_state()
        self.folder.mkdir(parents=True, exist_ok=True)

    def _load_state(self) -> Dict[str, str]:
        if self.state_path.exists():
            try:
                return json.loads(self.state_path.read_text(encoding="utf-8"))
            except Exception:
                return {}
        return {}

    def _save_state(self):
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        self.state_path.write_text(json.dumps(self.state, indent=2), encoding="utf-8")

    def _read_file(self, p: Path) -> str:
        reader = READERS.get(p.suffix.lower())
        if not reader:
            return ""
        text = reader(p)
        if not text:
            return ""
        return text[: self.chunk_limit]

    def tick(self) -> Dict[str, int]:
        added = 0
        updated = 0
        docs: List[str] = []
        metas: List[Dict] = []
        for p in self.folder.rglob("*"):
            if not p.is_file():
                continue
            if p.suffix.lower() not in READERS:
                continue
            text = self._read_file(p)
            if not text:
                continue
            fp = _fingerprint(text)
            key = str(p.resolve())
            if key not in self.state:
                added += 1
                self.state[key] = fp
                docs.append(text)
                metas.append({"path": key, "fp": fp})
            elif self.state[key] != fp:
                updated += 1
                self.state[key] = fp
                docs.append(text)
                metas.append({"path": key, "fp": fp})
        if docs:
            ingest_texts(docs, metas, collection=self.collection)
            self._save_state()
        return {"added": added, "updated": updated}

    def run_forever(self):
        while True:
            try:
                self.tick()
            except Exception:
                pass
            time.sleep(self.interval_s)


if __name__ == "__main__":
    print(CorpusWatcher().tick())
