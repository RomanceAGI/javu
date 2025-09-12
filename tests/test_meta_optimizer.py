from javu_agi.meta_optimizer import MetaOptimizer
def test_meta_optimizer_adjusts():
    mo = MetaOptimizer(path="run_data/_tmp_meta.json")
    t0 = mo.suggest()["temperature"]
    for _ in range(5):
        mo.update("blocked")
    assert mo.suggest()["temperature"] <= t0
