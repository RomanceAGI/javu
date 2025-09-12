from javu_agi.resilience_manager import ResilienceManager
def test_resilience_shed_load_when_cb_open():
    r = ResilienceManager()
    r.snapshot()
    r.cb_exec.open_until = 10**9
    assert r.should_shed_load() is True
