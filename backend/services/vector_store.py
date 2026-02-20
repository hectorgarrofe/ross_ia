import chromadb

from config.settings import get_settings
from backend.services.ollama_client import OllamaClient


class VectorStore:
    def __init__(self):
        settings = get_settings()
        self._client = chromadb.PersistentClient(
            path=str(settings.vectorstore_path)
        )
        self._collection = self._client.get_or_create_collection(
            name="ross_documents",
            metadata={"hnsw:space": "cosine"},
        )
        self._ollama = OllamaClient()

    @property
    def chunks_count(self) -> int:
        return self._collection.count()

    async def add_documents(
        self,
        texts: list[str],
        metadatas: list[dict],
        ids: list[str],
    ) -> None:
        if not texts:
            return

        # Embed in batches of 32 to avoid timeouts
        batch_size = 32
        all_embeddings = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            embeddings = await self._ollama.embed_batch(batch)
            all_embeddings.extend(embeddings)

        self._collection.add(
            documents=texts,
            embeddings=all_embeddings,
            metadatas=metadatas,
            ids=ids,
        )

    async def search(self, query: str, top_k: int | None = None) -> list[dict]:
        settings = get_settings()
        top_k = top_k or settings.retrieval_top_k

        if self._collection.count() == 0:
            return []

        query_embedding = await self._ollama.embed(query)

        results = self._collection.query(
            query_embeddings=[query_embedding],
            n_results=min(top_k, self._collection.count()),
            include=["documents", "metadatas", "distances"],
        )

        hits = []
        for i in range(len(results["documents"][0])):
            hits.append({
                "text": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "distance": results["distances"][0][i],
            })
        return hits

    def reset(self) -> None:
        self._client.delete_collection("ross_documents")
        self._collection = self._client.get_or_create_collection(
            name="ross_documents",
            metadata={"hnsw:space": "cosine"},
        )

    def get_document_names(self) -> list[str]:
        if self._collection.count() == 0:
            return []
        all_meta = self._collection.get(include=["metadatas"])
        names = {m.get("source", "unknown") for m in all_meta["metadatas"]}
        return sorted(names)
