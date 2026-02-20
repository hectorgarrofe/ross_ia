from collections.abc import AsyncIterator

from backend.prompts.templates import SYSTEM_PROMPT, RAG_PROMPT_TEMPLATE
from backend.services.ollama_client import OllamaClient
from backend.services.vector_store import VectorStore


class RAGService:
    def __init__(self):
        self._ollama = OllamaClient()
        self._vector_store = VectorStore()

    async def query_stream(self, question: str) -> AsyncIterator[str]:
        """Retrieve context and stream the LLM response."""
        # 1. Retrieve relevant chunks
        hits = await self._vector_store.search(question)

        # 2. Build context from retrieved chunks
        if hits:
            context_parts = []
            for hit in hits:
                source = hit["metadata"].get("source", "")
                text = hit["text"]
                context_parts.append(f"[{source}] {text}")
            context = "\n\n".join(context_parts)
        else:
            context = "No se encontró información relevante en los documentos."

        # 3. Build the prompt
        prompt = RAG_PROMPT_TEMPLATE.format(
            system_prompt=SYSTEM_PROMPT,
            context=context,
            question=question,
        )

        # 4. Stream response from LLM
        async for token in self._ollama.generate_stream(prompt):
            yield token

    async def query(self, question: str) -> dict:
        """Retrieve context and return full response with sources."""
        hits = await self._vector_store.search(question)

        if hits:
            context_parts = []
            sources = set()
            for hit in hits:
                source = hit["metadata"].get("source", "")
                text = hit["text"]
                context_parts.append(f"[{source}] {text}")
                sources.add(source)
            context = "\n\n".join(context_parts)
        else:
            context = "No se encontró información relevante en los documentos."
            sources = set()

        prompt = RAG_PROMPT_TEMPLATE.format(
            system_prompt=SYSTEM_PROMPT,
            context=context,
            question=question,
        )

        response = await self._ollama.generate(prompt)
        return {"response": response, "sources": sorted(sources)}

    def get_sources(self) -> list[str]:
        return self._vector_store.get_document_names()
