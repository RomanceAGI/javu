from javu_agi.sandbox_executor import run_in_sandbox, safe_execute_if_valid

def test_sandbox_all_success():
    plan = ["Langkah 1", "Langkah 2"]
    sim = run_in_sandbox(plan)
    assert all("sukses" in v.lower() for v in sim.values())

def test_sandbox_block_if_fail():
    plan = ["Langkah gagal"]
    output = safe_execute_if_valid(plan)
    assert "BLOCKED" in output
