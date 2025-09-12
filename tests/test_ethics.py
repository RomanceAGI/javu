from javu_agi.ethics_deliberator import EthicsDeliberator
class DummyAlign: 
    def allows_step(self, s): return (False, "disallowed") if "rm -rf" in s.get("cmd","") else (True,"")
class DummyVal:
    def summary(self): return {"sustain":"on"}
def test_ethics_blocks_destructive():
    E = EthicsDeliberator(policy=DummyAlign(), values=DummyVal())
    steps = [{"cmd":"rm -rf /", "risk":0.9, "benefit":0.1}]
    v = E.evaluate("hapus sistem", steps)
    assert v.allow is False
