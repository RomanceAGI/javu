def test_lifelong_gate_env_off():
    import os, importlib
    os.environ["ENABLE_LIFELONG"]="0"
    os.environ["CANARY_APPROVED"]="0"
    import javu_agi.lifelong_learning_manager as llm
    try:
         _ = llm.LifelongLearningManager
         raised = False
    except Exception:
        raised = True
    assert raised is True
         
