from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
import uuid


class VectorClient:
    def __init__(self, host="qdrant", port=6333):
        self.client = QdrantClient(host=host, port=port)
        self.collection = "agi_facts"
        self._ensure_collection()

    def _ensure_collection(self):
        if self.collection not in self.client.get_collections().collections:
            self.client.create_collection(
                collection_name=self.collection,
                vectors_config=VectorParams(size=768, distance=Distance.COSINE),
            )

    def upsert(self, text: str, embedding: list, metadata: dict):
        pid = str(uuid.uuid4())
        self.client.upsert(
            collection_name=self.collection,
            points=[PointStruct(id=pid, vector=embedding, payload=metadata)],
        )

    def search(self, embedding: list, limit=5):
        res = self.client.search(
            collection_name=self.collection, query_vector=embedding, limit=limit
        )
        return [r.payload for r in res]
