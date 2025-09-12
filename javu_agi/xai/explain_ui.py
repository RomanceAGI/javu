from __future__ import annotations
import html, json, os, time
from typing import Dict, Any

TEMPLATE = """<!doctype html>
<meta charset="utf-8">
<title>XAI · {title}</title>
<style>
body{font-family:ui-sans-serif,system-ui,Segoe UI,Arial;margin:24px;color:#0a0a0a}
h1{font-size:20px;margin:0 0 12px}
.card{border:1px solid #e5e7eb;border-radius:12px;padding:16px;margin:12px 0;box-shadow:0 1px 2px rgba(0,0,0,.04)}
pre{white-space:pre-wrap;word-break:break-word;background:#f9fafb;padding:12px;border-radius:8px}
.kv{display:grid;grid-template-columns:160px 1fr;gap:8px}
.kv div:first-child{color:#6b7280}
.badge{display:inline-block;padding:2px 8px;border-radius:9999px;background:#eef2ff;color:#3730a3;font-size:12px}
</style>
<h1>{title}</h1>
<div class="kv">
  <div>Episode</div><div>{episode}</div>
  <div>Trace</div><div>{trace}</div>
  <div>Status</div><div><span class="badge">{status}</span></div>
</div>
<div class="card"><b>Plan Steps</b><pre>{steps}</pre></div>
<div class="card"><b>Affect Weights</b><pre>{affect}</pre></div>
<div class="card"><b>Impact Scores</b><pre>{impact}</pre></div>
<div class="card"><b>Gates</b><pre>{gates}</pre></div>
<div class="card"><b>Explainer</b><pre>{expl}</pre></div>
<footer style="color:#6b7280;margin-top:24px">Generated {ts}</footer>
"""


def render(payload: Dict[str, Any]) -> str:
    def _fmt(x):
        try:
            return html.escape(json.dumps(x, ensure_ascii=False, indent=2))
        except Exception:
            return html.escape(str(x))

    return TEMPLATE.format(
        title=html.escape(str(payload.get("provenance_tag", "explain"))),
        episode=html.escape(str(payload.get("episode_id", "-"))),
        trace=html.escape(str(payload.get("trace_id", "-"))),
        status=html.escape(str(payload.get("status", "-"))),
        steps=_fmt(payload.get("plan_steps", [])),
        affect=_fmt(payload.get("affect_weights", {})),
        impact=_fmt(payload.get("impact_scores", {})),
        gates=_fmt(payload.get("gates", {})),
        expl=_fmt(payload.get("explainer_dict", {})),
        ts=time.strftime("%Y-%m-%d %H:%M:%S"),
    )


def write(payload: Dict[str, Any], out_dir: str = "artifacts/xai") -> Dict[str, str]:
    os.makedirs(out_dir, exist_ok=True)
    base = os.path.join(
        out_dir, f'{payload.get("episode_id","ep")}_{payload.get("trace_id","trace")}'
    )
    html_path = base + ".html"
    try:
        open(html_path, "w", encoding="utf-8").write(render(payload))
    except Exception:
        pass
    return {"html": html_path}
