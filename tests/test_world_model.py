from javu_agi.world_model import WorldModel

def test_do_intervene_confidence():
    wm = WorldModel()
    base = wm.do_intervene({"ambiguity": 0.9}, probe="confidence")
    better = wm.do_intervene({"ambiguity": 0.1}, probe="confidence")
    assert better >= base
