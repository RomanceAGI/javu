from javu_agi.self_diagnose_and_upgrade import self_diagnose_and_upgrade

def test_self_diagnose():
    upgrades = self_diagnose_and_upgrade("test_user")
    assert isinstance(upgrades, list)
