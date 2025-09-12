from javu_agi.learn.policy_learner_ctx import ContextualPolicyLearner

def test_linucb_update():
    L = ContextualPolicyLearner(dim=8)
    x = [1,0.2,0.3,0.1,1,0,0,0]
    arm = L.choose(x)["arm"]
    L.record(arm, x, 1.0)
    arm2 = L.choose(x)["arm"]
    assert arm2 in ["S1","S2","S3"]
