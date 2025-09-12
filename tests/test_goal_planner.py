def test_goal_generation():
    from javu_agi.goal_planner import GoalPlanner
    planner = GoalPlanner()
    goal = planner.generate_goal("User wants to learn Python")
    assert "python" in goal.lower()
