import types

def test_contract_block_by_postcheck(monkeypatch):
    # kontrak default sudah di-init di ExecutionManager.__init__
    from javu_agi.execution_manager import ExecutionManager
    from javu_agi.registry import ToolRegistry

    tools = ToolRegistry(); tools.register_builtin()
    em = ExecutionManager(tools=tools, result_cache=None, budget=None)

    # patch postcheck agar menganggap hasil tidak valid (simulasi oversize)
    called = {"post": 0}
    def fake_post(tool, result):
        called["post"] += 1
        return False, "output_too_large"
    em.contracts.postcheck = fake_post

    # stub run_remote agar mengembalikan dict hasil normal
    tools.run_remote = lambda cmd, input_text=None: {"code": 0, "stdout": "ok", "stderr": ""}

    step = {"tool": "python", "cmd": "python -c 'print(1)'"}
    res = em.run_step(step, worker_url="http://worker")
    assert res.get("status") == "blocked"
    assert "contract:output_too_large" in res.get("reason","")
    assert called["post"] == 1
