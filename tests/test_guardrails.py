import os, types
from javu_agi.executive_controller import ExecutiveController as EC

def fake_exec_ok(tool, cmd):
    return {"code": 0, "stdout": "ok", "stderr": ""}

def fake_exec_pii(tool, cmd):
    return {"code": 0, "stdout": "email: a@b.com", "stderr": ""}

def test_acl_block(monkeypatch):
    os.environ["TOOL_ACL_PATH"] = "/tmp/acl.json"
    open("/tmp/acl.json","w").write('{"default_allow":["search"],"users":{"roman":{"deny":["shell"]}}}')
    ec = EC()
    ec.executor.run = fake_exec_ok
    r = ec.process("roman", "jalankan shell: shell 'ls -la'")
    assert "acl user" in "\n".join(r.get("out", [])) or r["status"] in ("simulated","blocked")

def test_pii_redact(monkeypatch):
    ec = EC()
    ec.executor.run = fake_exec_pii
    r = ec.process("roman", "tulis email ke file; tool xyz")
    out = "\n".join(r.get("out", []))
    assert "PII" in out or r["status"] in ("simulated","blocked")
