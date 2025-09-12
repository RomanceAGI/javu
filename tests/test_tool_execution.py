def test_tool_code_gen():
    from javu_agi.tool_code_gen import CodeGenTool
    tool = CodeGenTool()
    code = tool.generate_code("print hello world")
    assert "print" in code and "hello" in code.lower()
