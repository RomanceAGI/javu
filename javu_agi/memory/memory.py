from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
import os

CHROMA_DIR = "db/chroma_memory"
embedding_function = HuggingFaceEmbeddings(
    model_name=os.getenv("MEM_EMB_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
)


def get_chroma_db(user_id):
    persist_path = os.path.join(CHROMA_DIR, user_id)
    os.makedirs(persist_path, exist_ok=True)
    return Chroma(persist_directory=persist_path, embedding_function=embedding_function)


def save_to_memory(data, user_id):
    from javu_agi.logger import log_user

    db = get_chroma_db(user_id)
    text = str(data)
    tag: None
    if "[" in text and "]" in text:
        try:
            tag = text.split("[", 1)[1].split("]", 1)[0]
        except Exception:
            tag = None
    meta = {"ts": int(time.time())}
    if tag:
        meta["tag"] = tag
    db.add_documents([Document(page_content=text, metadata=meta)])
    log_user(user_id, f"[MEMORY] store tag={tag} len={len(text)}")


def recall_from_memory(user_id, query: str, top_k=3, tag: str | None = None):
    db = get_chroma_db(user_id)
    if tag:
        docs = db._collection.get(include=["metadatas", "documents"])
        pairs = list(zip(docs["metadatas"], docs["documents"]))
        filt = [d for m, d in pairs if m and m.get("tag") == tag]
        return "\n".join(filt[-top_k:]) if filt else ""
    retriever = db.as_retriever(search_kwargs={"k": top_k})
    results = retriever.invoke(query or "")
    return "\n".join([doc.page_content for doc in results])


def update_memory_from_interaction(user_id, user_input, agent_output):
    combined = f"User: {user_input}\nJAVU: {agent_output}"
    save_to_memory(user_id, combined)
