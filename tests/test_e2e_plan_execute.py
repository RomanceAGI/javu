def test_e2e_plan_execute(monkeypatch):
    from javu_agi.executive_controller import ExecutiveController
    ec = ExecutiveController()
    # stub berat
    ec.adv_guard.scan_prompt = lambda p: {"ok": True}
    ec.optimizer.optimize = lambda s: s
    ec.peace_opt.optimize = lambda s: s
    ec.tracer.log = lambda *a, **k: None
    ec.expl_reporter.write = lambda p: None
    ec.explainer.explain = lambda *a, **k: {}

    out = ec.maybe_plan_and_execute("u", "print angka satu", context={})
    assert isinstance(out, dict)
