from javu_agi.core_loop import run_user_loop

def test_core_loop_executes():
    response = run_user_loop("test_user", "Ceritakan tentang AGI", None)
    assert isinstance(response, str)
    assert len(response) > 0
