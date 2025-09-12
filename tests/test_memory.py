def test_memory_store_and_recall():
    from javu_agi.memory.memory import Memory
    user="test_user"
    memory.save_to_memory("[NOTE] The sky is blue.", user)
    res = memory.recall_from_memory(user, "sky blue", top_k=3)
    assert "blue" in res.lower()
