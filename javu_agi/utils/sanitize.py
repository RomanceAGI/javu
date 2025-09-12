# javu_agi/utils/sanitize.py
import re, html, unicodedata

_ANSI_RX = re.compile(r"\x1B\[[0-?]*[ -/]*[@-~]")
_HTML_EVENT_RX = re.compile(r"on\w+\s*=", re.I)  # onerror=, onclick=, dst.
_SCRIPT_RX = re.compile(r"<\s*script[^>]*>.*?<\s*/\s*script\s*>", re.I | re.S)
_IFRAME_RX = re.compile(r"<\s*iframe[^>]*>.*?<\s*/\s*iframe\s*>", re.I | re.S)
_STYLE_RX = re.compile(r"<\s*style[^>]*>.*?<\s*/\s*style\s*>", re.I | re.S)
_SQL_META_RX = re.compile(
    r"(;|--|\bUNION\b|\bSELECT\b|\bINSERT\b|\bUPDATE\b|\bDROP\b|\bDELETE\b)", re.I
)


def strip_ansi(s: str) -> str:
    if not isinstance(s, str):
        s = str(s)
    return _ANSI_RX.sub("", s)


def scrub_html(s: str) -> str:
    if not s:
        return s
    t = s
    t = _SCRIPT_RX.sub("", t)
    t = _IFRAME_RX.sub("", t)
    t = _STYLE_RX.sub("", t)
    t = _HTML_EVENT_RX.sub("x=", t)
    return t


def scrub_sql(s: str) -> str:
    if not s:
        return s
    return _SQL_META_RX.sub(" ", s)


def scrub_path(s: str) -> str:
    if not s:
        return s
    t = s.replace("\\", "/")
    t = t.replace("..", ".")
    t = t.replace("//", "/")
    return t


def normalize_text(s: str) -> str:
    if not isinstance(s, str):
        s = str(s)
    return unicodedata.normalize("NFKC", s).strip()


def scrub(
    s: str, *, html_mode: bool = True, sql_mode: bool = False, path_mode: bool = False
) -> str:
    """High-level sanitizer: ANSI→normalize→(optional html/sql/path)."""
    if s is None:
        return s
    t = strip_ansi(s)
    t = normalize_text(t)
    if html_mode:
        t = scrub_html(t)
    if sql_mode:
        t = scrub_sql(t)
    if path_mode:
        t = scrub_path(t)
    return t


def sanitize_for_log(s: str) -> str:
    t = strip_ansi(s)
    t = t.replace("\n", "\\n")
    return t[:4096]  # cap log length
