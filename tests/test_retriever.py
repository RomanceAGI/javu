from javu_agi.rag.ingest import ingest_texts
from javu_agi.rag.retriever import HybridRetriever

def test_hybrid_retriever():
    facts = []
    R = HybridRetriever(facts_ref=lambda: facts)
    ingest_texts(["Langit biru karena Rayleigh scattering."],[{}])
    out = R.retrieve("mengapa langit biru", k=4)
    assert out, "should recall something"
