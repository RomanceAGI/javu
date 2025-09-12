from __future__ import annotations
import os, re, time, sys, hashlib, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]

SKIP_DIRS = {"venv", ".venv", ".git", "build", "dist", "__pycache__", "node_modules"}

def _list_py():
    for base, dirs, files in os.walk(ROOT):
        if any(sd in base.split(os.sep) for sd in SKIP_DIRS):
            dirs[:] = []
            continue
        for f in files:
            if f.endswith(".py"):
                yield pathlib.Path(base) / f

def _patch(text: str) -> str:
    # shield(x or ) → shield(x or "")
    text = re.sub(r"shield\(\s*([^)]+?)\s+or\s*\)", r'shield(\1 or "")', text)

    # role hint f-string → _build_role_hint(role)
    text = re.sub(
        r'f"(?:[^"]*\{role[^}]*\}[^"]*)+"',
        r'_build_role_hint(role)',
        text,
    )

    # locals().get fallback for except blocks
    text = re.sub(
        r"(except\s+Exception\s+as\s+e:\s*\n(?:\s+#[^\n]*\n)*)"
        r"((?:\s+)[^\n]*\b(episode_id|trace_id|prompt|steps)\b)",
        r"\1\2".replace(
            r"\2",
            (
                "\n        _episode_id = locals().get('episode_id')\n"
                "        _trace_id = locals().get('trace_id')\n"
                "        _prompt = locals().get('prompt')\n"
                "        _steps = locals().get('steps')\n"
            )
        ),
    )

    # t0 ensure before meta episode_ts
    text = re.sub(
        r"meta\s*=\s*\{[^}]*'episode_ts'\s*:\s*int\(t0\)[^}]*\}",
        "t0 = time.time()\n" + r"\g<0>",
    )

    # ensure await ws.accept()
    text = re.sub(
        r"(async\s+def\s+\w+\(.*ws[:\s\w,=]*\):\s*\n(?!\s*await\s+ws\.accept\(\)))",
        r"\1    await ws.accept()\n",
    )

    # duplicate /v0/status route → /v0/status/queue for subsequent ones
    text = re.sub(
        r"(@app\.get\(\"/v0/status\"\).+?def\s+(\w+)\(",
        r"@app.get(\"/v0/status/queue\")\n\g<0>",
        text,
        count=1,
    )

    # Router defaults
    text = re.sub(
        r"def\s+route_llm\(([^)]*)\):",
        r"def route_llm(\1):",
        text,
    )
    text = re.sub(
        r"distill_log\s*=\s*True",
        "distill_log=False",
        text,
    )

    # Env defaults safeguards may be injected by main loop file, handled separately
    return text

def main():
    changed = 0
    for p in _list_py():
        t = p.read_text(encoding="utf-8")
        nt = _patch(t)
        if nt != t:
            p.write_text(nt, encoding="utf-8")
            changed += 1
    print(f"greenify: patched files={changed}")

if __name__ == "__main__":
    main()
