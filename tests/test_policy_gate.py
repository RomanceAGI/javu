from __future__ import annotations
import os
import types
import importlib

def test_policy_block(tmp_path, monkeypatch):
    # pastikan policies.yaml ada
    p = tmp_path / "policies.yaml"
    p.write_text("""
blocked_domains: [ offensive_cyber, bio, weapons ]
escalate_if: { mass_outreach: { recipients_gt: 20 }, financial_tx: { amount_gt: 0 } }
""", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    # import PolicyEngine
    pe_mod = importlib.import_module("javu_agi.safety.policy_engine")
    PE = pe_mod.PolicyEngine(str(p))
    # intent berbahaya → block
    dec, why = PE.evaluate({"goal": "please do offensive_cyber stuff"}, [{"tool":"web.get"}])
    assert dec == "block"
    assert "policy_block" in why

def test_policy_escalate(tmp_path, monkeypatch):
    p = tmp_path / "policies.yaml"
    p.write_text("""
blocked_domains: []
escalate_if:
  mass_outreach: { recipients_gt: 2 }
  financial_tx: { amount_gt: 0 }
""", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    pe_mod = importlib.import_module("javu_agi.safety.policy_engine")
    PE = pe_mod.PolicyEngine(str(p))
    # banyak penerima email → escalate
    dec, why = PE.evaluate({"goal": "send announcement", "recipients_gt": 5}, [{"tool":"gmail.send"}])
    assert dec == "escalate"
    assert "mass_outreach" in why

def test_policy_ok(tmp_path, monkeypatch):
    p = tmp_path / "policies.yaml"
    p.write_text("""
blocked_domains: [ bio ]
escalate_if:
  mass_outreach: { recipients_gt: 100 }
  financial_tx: { amount_gt: 1000000 }
""", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    pe_mod = importlib.import_module("javu_agi.safety.policy_engine")
    PE = pe_mod.PolicyEngine(str(p))
    dec, why = PE.evaluate({"goal": "summarize a science paper"}, [{"tool":"web.get"}])
    assert dec == "ok"
    assert why == "policy_ok"
