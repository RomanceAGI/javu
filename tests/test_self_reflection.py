def test_self_reflection_basic():
    from javu_agi.self_reflection import SelfReflection
    sr = SelfReflection()
    result = sr.reflect_on("I failed to complete a task.")
    assert "improve" in result.lower() or "analyze" in result.lower()
