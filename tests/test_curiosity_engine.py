from javu_agi.curiosity_engine import suggest_exploration_goal, rank_information_novelty

def test_suggest_goal():
    goal = suggest_exploration_goal(["JAVU: sudah tahu semua"])
    assert isinstance(goal, str)

def test_rank_novelty():
    ranked = rank_information_novelty(["X", "XYZ", "XX"])
    assert ranked[0] == "XYZ"
