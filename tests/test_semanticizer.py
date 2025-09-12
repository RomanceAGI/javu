from javu_agi.memory.semanticizer import abstract_from_memory

def test_abstract_from_memory():
    abstract = abstract_from_memory("test_user")
    assert isinstance(abstract, list)
    assert all(isinstance(x, str) for x in abstract)
