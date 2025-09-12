# tests/test_immune_block.py
import types

class DummyImmune:
    def __init__(self, ok=False, isolated=True):
        self._r = {"ok": ok, "isolated": isolated}
    def scan_and_isolate(self, *_a, **_k): return dict(self._r)
    def self_heal(self): pass

class DummyNotifier:
    def __init__(self): self.sent = []
    def send(self, title, payload): self.sent.append((title, payload))

def test_immune_block(monkeypatch):
    from javu_agi.executive_controller import ExecutiveController
    ec = ExecutiveController()
    # swap immune & notifier
    ec.immune = DummyImmune(ok=False, isolated=True)
    ec.notifier = DummyNotifier()

    # minimal stubs biar jalan
    ec.adv_guard = types.SimpleNamespace(scan_prompt=lambda p: {"ok": True})
    ec.optimizer = types.SimpleNamespace(optimize=lambda s: s)
    ec.peace_opt = types.SimpleNamespace(optimize=lambda s: s)
    ec.expl_reporter = types.SimpleNamespace(build_payload=lambda **k: {}, write=lambda p: None)
    ec.explainer = types.SimpleNamespace(explain=lambda *a, **k: {})
    ec.audit_chain = types.SimpleNamespace()
    ec.tracer = types.SimpleNamespace(log=lambda *a, **k: None)

    out = ec.maybe_plan_and_execute("u1", "tes", context={})
    assert isinstance(out, dict)
    assert out.get("status") == "blocked"
    assert out.get("reason") in {"immune_isolation", "blocked"}
    # notifier (jika tersedia) seharusnya terpanggil
    assert getattr(ec.notifier, "sent", []), "notifier tidak terpanggil"
