from __future__ import annotations
import os, json, importlib, time
from pathlib import Path

def test_xai_report_writes_html_and_jsonl(tmp_path, monkeypatch):
    # set output dir XAI
    out = tmp_path / "xai"
    monkeypatch.setenv("XAI_DIR", str(out))

    # siapkan EC minimal
    ec_mod = importlib.import_module("javu_agi.executive_controller")
    EC = ec_mod.ExecutiveController

    ec = EC()  # asumsi EC bisa init tanpa env berat
    # panggil _xai_report langsung (pakai signature yang lo punya)
    ec._xai_report(
        tag="unit_test",
        status="ok",
        steps=[{"tool":"web.get","args":{"url":"https://example.com"}}],
        affect_weights={"prosocial_weight":1.0},
        impact_scores={"sustainability":0.9},
        gates={"adv_guard":"pass"},
        chosen={"summary":"done"},
        candidates=[{"option":"A"}],
        episode_id="ep1",
        trace_id=f"trace_{int(time.time())}"
    )

    # verifikasi artefak
    files = list(Path(out).glob("*.html"))
    assert files, "HTML XAI tidak tertulis"
    # cari jsonl dengan nama trace
    jsonls = list(Path(out).glob("*.jsonl"))
    assert jsonls, "JSONL XAI tidak tertulis"
    # valid json di baris terakhir
    with open(jsonls[-1], "r", encoding="utf-8") as f:
        last = [l for l in f.readlines() if l.strip()][-1]
        obj = json.loads(last)
        assert obj.get("status") == "ok"
        assert obj.get("trace_id")
