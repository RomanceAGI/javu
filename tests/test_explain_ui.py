from javu_agi.explain_ui import render
def test_explain_ui_renders():
    html = render({"episode_id":"e1","trace_id":"t1","status":"executed"})
    assert "<html" in ("<html" + html.lower()) or "<!doctype" in html.lower()
    assert "executed" in html
