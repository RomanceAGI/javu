from __future__ import annotations
import os, json, time, html
from typing import Dict, Any, List, Optional


class ExplanationReporter:
    """
    Ngumpulin jejak keputusan dari EC:
    - plan terpilih, alternatif & skor
    - bobot nilai (affect/moral/justice) + impact assessor
    - alasan (explainer), gate (ethics/peace/commons)
    - audit chain head + provenance snapshot tag
    Output: .json + .html ringkas
    """

    def __init__(self, out_dir: str = "reports"):
        self.out_dir = out_dir
        os.makedirs(self.out_dir, exist_ok=True)

    def build_payload(
        self,
        *,
        episode_id: str,
        trace_id: str,
        plan_steps: List[Dict[str, Any]],
        chosen: Dict[str, Any] | None,
        candidates: List[Dict[str, Any]] | None,
        affect_weights: Dict[str, float] | None,
        impact_scores: Dict[str, float] | None,
        gates: Dict[str, Any] | None,
        explainer_dict: Dict[str, Any] | None,
        audit_head: str | None,
        provenance_tag: str | None,
        status: str,
    ) -> Dict[str, Any]:
        return {
            "ts": int(time.time()),
            "episode": episode_id,
            "trace": trace_id,
            "status": status,
            "plan": {
                "chosen": chosen or {},
                "steps": plan_steps or [],
                "candidates": candidates or [],
            },
            "weights": affect_weights or {},
            "impact": impact_scores or {},
            "gates": gates or {},
            "explainer": explainer_dict or {},
            "audit": {"head": audit_head},
            "provenance": {"tag": provenance_tag},
        }

    def _html_row(self, k: str, v: Any) -> str:
        val = html.escape(json.dumps(v, ensure_ascii=False, indent=2))
        return f"<tr><td style='font-weight:600'>{html.escape(k)}</td><td><pre>{val}</pre></td></tr>"

    def to_html(self, payload: Dict[str, Any]) -> str:
        rows = []
        rows.append(self._html_row("episode", payload.get("episode")))
        rows.append(self._html_row("trace", payload.get("trace")))
        rows.append(self._html_row("status", payload.get("status")))
        rows.append(
            self._html_row("chosen_plan", payload.get("plan", {}).get("chosen"))
        )
        rows.append(self._html_row("steps", payload.get("plan", {}).get("steps")))
        rows.append(
            self._html_row("candidates", payload.get("plan", {}).get("candidates"))
        )
        rows.append(self._html_row("weights", payload.get("weights")))
        rows.append(self._html_row("impact", payload.get("impact")))
        rows.append(self._html_row("gates", payload.get("gates")))
        rows.append(self._html_row("explainer", payload.get("explainer")))
        rows.append(self._html_row("audit", payload.get("audit")))
        rows.append(self._html_row("provenance", payload.get("provenance")))
        body = "\n".join(rows)
        return f"""<!doctype html>
<html><head><meta charset="utf-8"><title>XAI Report {html.escape(str(payload.get("episode")))}</title>
<style>body{{font-family:system-ui,Segoe UI,Roboto,Arial}} table{{border-collapse:collapse;width:100%}}
td{{border:1px solid #eee;vertical-align:top;padding:8px}}</style></head>
<body><h2>Explanation Report</h2><table>{body}</table></body></html>"""

    def write(self, payload: Dict[str, Any]) -> Dict[str, str]:
        eid = payload.get("episode") or f"ep_{int(time.time())}"
        rid = payload.get("trace") or "trace"
        base = os.path.join(self.out_dir, f"{eid}_{rid}")
        jpath = base + ".json"
        hpath = base + ".html"
        with open(jpath, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        with open(hpath, "w", encoding="utf-8") as f:
            f.write(self.to_html(payload))
        return {"json": jpath, "html": hpath}
