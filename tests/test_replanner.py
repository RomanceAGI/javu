from javu_agi.replanner import detect_plan_failure, generate_alternative_plan

def test_detect_plan_failure():
    fail = detect_plan_failure("Percobaan gagal total")
    success = detect_plan_failure("Semua berjalan baik")
    assert fail is True
    assert success is False

def test_generate_alternative_plan():
    alt = generate_alternative_plan("Bangun model AGI sejati")
    assert isinstance(alt, list)
    assert len(alt) > 0
