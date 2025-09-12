from javu_agi.tools.adapters.web_adapter import WebAdapter
def test_web_block_by_allowlist(monkeypatch):
    wa = WebAdapter()
    out = wa.get("https://not-allowed.example.com")
    assert out["status"] in {"blocked","error"}
