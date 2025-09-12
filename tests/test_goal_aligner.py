from javu_agi.goal_aligner import track_goal_context, validate_subgoal_consistency

def test_track_context():
    history = ["[GOAL] Jadi AGI", "[OTHER] ...", "[GOAL] Dominasi dunia"]
    ctx = track_goal_context(history)
    assert "→" in ctx

def test_subgoal_validation():
    assert validate_subgoal_consistency(["Belajar logika", "Latih diri"], "Menjadi cerdas")
