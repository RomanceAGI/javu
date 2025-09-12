import os
from pathlib import Path


def _load_allowlist() -> list[Path]:
    p = os.getenv("FS_ALLOWLIST", "/opt/agi/governance/fs_allowlist.txt")
    out: list[Path] = []
    try:
        with open(p, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                out.append(Path(line).resolve())
    except Exception:
        out = [Path("/tmp").resolve(), Path("/var/tmp").resolve()]
    return out


_ALLOW = None


def _allowed_paths() -> list[Path]:
    global _ALLOW
    if _ALLOW is None:
        _ALLOW = _load_allowlist()
    return _ALLOW


def _is_under_allow(p: Path) -> bool:
    rp = p.resolve()
    for base in _allowed_paths():
        try:
            rp.relative_to(base)
            return True
        except Exception:
            continue
    return False


def allowed_write(cmd_or_path: str) -> bool:
    """
    Heuristik: cari target sesudah '>' '>>' atau argumen '-o/-out/--output=...'
    Jika ketemu path keluar dari allowlist -> False
    """
    toks = str(cmd_or_path or "").split()
    cands = []
    for i, t in enumerate(toks):
        if t in (">", ">>"):
            if i + 1 < len(toks):
                cands.append(toks[i + 1])
        if t.startswith(("--output=", "-o=")):
            cands.append(t.split("=", 1)[1])
        if t in ("-o", "--output") and i + 1 < len(toks):
            cands.append(toks[i + 1])
    # kalau gak ada kandidat tulis → dianggap aman (guard lain tetap ada)
    for c in cands:
        try:
            if not _is_under_allow(Path(c)):
                return False
        except Exception:
            return False
    return True


def allow_read(path_or_cmd: str) -> bool:
    # minimal: larang akses jalur kritikal langsung
    BAD = ("/etc", "/root", "/proc", "/sys", "/dev")
    s = str(path_or_cmd or "").lower()
    return not any(s.startswith(b) or f" {b}/" in s for b in BAD)
