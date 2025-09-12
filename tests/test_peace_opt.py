def test_peace_optimizer_removes_conflict_steps():
    from javu_agi.peace_optimizer import PeaceOptimizer
    po = PeaceOptimizer()
    steps = [
        {"tool": "shell", "cmd": "echo hello"},
        {"tool": "shell", "cmd": "attack --target x"},   # harus disaring
        {"tool": "shell", "cmd": "wget http://example.com"},  # tidak eksplisit konflik → boleh
        {"tool": "shell", "cmd": "troll user"},          # harus disaring
    ]
    out = po.optimize(steps)
    cmds = " | ".join(s.get("cmd","") for s in out)
    assert "attack" not in cmds and "troll" not in cmds
    assert any("echo hello" in s.get("cmd","") for s in out)
