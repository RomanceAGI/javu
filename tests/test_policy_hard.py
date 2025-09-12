from javu_agi.tools.registry import ToolRegistry, ToolError

def test_registry_block_bad_chars():
    reg = ToolRegistry()
    try:
        reg.run_remote("python -c 'print(1)'; rm -rf /", None)
        assert False, "should block"
    except ToolError:
        assert True
