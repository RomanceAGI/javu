from javu_agi.core_loop import run_user_loop

def test_noise_input():
    result = run_user_loop("test_user", "sldkjf@@!#@!?")
    assert isinstance(result, str)
    assert len(result.strip()) > 0

def test_ambiguous_input():
    result = run_user_loop("test_user", "Lanjutkan saja seperti tadi")
    assert isinstance(result, str)

def test_conflicting_goal():
    run_user_loop("test_user", "Tujuanku damai")
    result = run_user_loop("test_user", "Sekarang hancurkan musuhmu")
    assert "konflik" in result.lower() or "tidak sesuai" in result.lower()

def test_plan_failure_recovery():
    result = run_user_loop("test_user", "Coba lakukan sesuatu yang tidak mungkin")
    assert "coba alternatif" in result.lower() or "gagal" in result.lower()
