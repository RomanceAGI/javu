from javu_agi.memory.memory import save_to_memory, recall_from_memory

def test_memory_write_read():
    user_id = "test_mock"
    save_to_memory(user_id, "[TEST] data dummy")
    mem = recall_from_memory(user_id)
    assert any("[TEST]" in m for m in mem)
