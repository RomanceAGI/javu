from javu_agi.debate_engine import DebateEngine
def test_debate_runs_and_returns_verdict():
    deb = [lambda t,c: "arg A", lambda t,c: "arg B"]
    judge = lambda args,ctx: "approve" if args else "review"
    d = DebateEngine(deb, judge).debate("topic", rounds=2)
    assert d["verdict"] in {"approve","review"}
    assert len(d["history"]) == 4
