from javu_agi.self_upgrader import analyze_internal_limitations, propose_architecture_modifications

def test_limit_analyzer():
    logs = ["Semua baik", "Ada kesalahan pada modul memory"]
    limits = analyze_internal_limitations(logs)
    assert any("kesalahan" in l for l in limits)

def test_upgrade_proposal():
    limits = ["Modul X gagal"]
    mods = propose_architecture_modifications(limits)
    assert len(mods) > 0
