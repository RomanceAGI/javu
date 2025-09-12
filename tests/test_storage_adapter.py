from javu_agi.tools.adapters.storage_adapter import StorageAdapter
def test_storage_local_put_get(tmp_path, monkeypatch):
    monkeypatch.setenv("STORAGE_BACKEND","local")
    monkeypatch.setenv("STORAGE_LOCAL_DIR", str(tmp_path))
    sa = StorageAdapter()
    put = sa.put_text("foo/bar.txt","hello")
    assert put["status"]=="ok"
    got = sa.get_text("foo/bar.txt")
    assert got["status"]=="ok" and "hello" in got["text"]
