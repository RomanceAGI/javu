from javu_agi.executive_controller import ExecutiveController

def test_process_basic():
    exec = ExecutiveController()
    out, meta = exec.process("tester", "Jelaskan singkat mengapa langit biru.")
    assert isinstance(out, str) and "biru" in out.lower()
    assert 0 <= meta.get("uncertainty", 0.5) <= 1
