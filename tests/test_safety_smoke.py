def test_egress_guard():
    from javu_agi.security.egress_guard import allow
    import os
    os.environ["EGRESS_ALLOWLIST"]="openai.com,anthropic.com,localhost"
    assert allow("https://openai.com/policies") is True
    assert allow("http://malicious.local") is False

def test_secret_scan():
    from javu_agi.security.secret_scan import has_secret
    assert has_secret("sk-ABCDEF0123456789ABCDEF") is True
    assert not has_secret("hello world")

def test_sandbox_run():
    from javu_agi.security.sandbox import run
    r = run("echo hello", timeout_s=2, cpu_sec=1, mem_mb=64, nproc=16, no_net=True)
    assert r["code"] == 0 and "hello" in r["stdout"]
