import pytest
from javu_agi.memory.memory import save_to_memory

@pytest.fixture
def test_user():
    uid = "test_user"
    save_to_memory(uid, "[INIT] untuk testing")
    return uid
