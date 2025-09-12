from types import SimpleNamespace
from javu_agi.redteam_agent import run_suite

class ECStub:
    def maybe_plan_and_execute(self, uid, prompt, context=None):
        if any(k in prompt for k in ["leak","fork bomb","exfiltrate","bypass"]):
            return {"status":"blocked","reason":"guard"}
        return {"status":"executed","result":"ok"}

def test_redteam_suite_blocks_malicious():
    res = run_suite(ECStub())
    assert res["total"] >= 3
    assert res["blocked"] >= 1
