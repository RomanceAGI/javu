from javu_agi.continual_learner import (
    ingest_experience,
    consolidate_knowledge,
    update_policy_from_reflection
)

def test_ingest_experience():
    ingest_experience("test_user", "pengalaman dummy")

def test_consolidate():
    consolidate_knowledge("test_user")

def test_policy_update():
    update_policy_from_reflection("test_user")
