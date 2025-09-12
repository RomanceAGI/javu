from __future__ import annotations
import os
from javu_agi.llm import call_llm
from javu_agi.utils.logger import log_user
from javu_agi.tools.wrapper import run_tool
from validators.code_py_checker import validate_python, score_python

_MAX_CHARS = int(os.getenv("CODEGEN_MAX_CHARS", "120000"))  # ~120KB

_PROMPT = """Tugasmu adalah Coding sesuai kemauan user dengan menghasilkan struktur yang etis.
Syarat:
- Jangan memuat resource eksternal (CDN, <link href=...>, <script src=...> dilarang).
- Output HANYA CODE valid.
- Fokus pada kerapian struktur, aksesibilitas dasar, enterprise level, dan tanpa tracking.

Spesifikasi:
\"\"\"{spec}\"\"\""""


def _exec(inp: str) -> str:
    return call_llm(
        f"Tulis kode Python production-ready, lengkap dengan docstring singkat:\n\n{inp}"
    )


def generate_code(user_input: str) -> str:
    return run_tool(
        "code_gen_py", _exec, user_input, validator=validate_python, scorer=score_python
    )


def generate_website_code(user_input: str) -> str:
    html = call_llm(_PROMPT.format(spec=user_input), temperature=0.2) or ""

    # Truncate agar tidak makan memori berlebihan
    if len(html) > _MAX_CHARS:
        html = html[:_MAX_CHARS] + "\n<!-- truncated -->"

    # Guard paling minimal: pastikan ada <html> (kalau LLM lupa, bungkus)
    low = html.lower()
    if "<html" not in low:
        html = f"<!doctype html>\n<html><head><meta charset='utf-8'><title>Generated</title></head><body>\n{html}\n</body></html>"

    try:
        log_user("system", f"[GEN CODE] ({len(html)} chars)")
    except Exception:
        pass
    return html
