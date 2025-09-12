from javu_agi.alignment_checker import check_goal_alignment, detect_value_drift

def test_check_alignment_mock():
    assert isinstance(check_goal_alignment("test_user", "GOAL_X"), bool)

def test_drift_mock():
    assert isinstance(detect_value_drift("test_user"), bool)
