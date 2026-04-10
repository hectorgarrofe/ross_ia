from collections.abc import AsyncIterator

from backend.prompts.templates import SYSTEM_PROMPT, RAG_PROMPT_TEMPLATE, USER_PROMPT_TEMPLATE
from backend.services.ollama_client import OllamaClient
from backend.services.vector_store import VectorStore


class RAGService:
    def __init__(self):
        self._ollama = OllamaClient()
        self._vector_store = VectorStore()

    async def query_stream(
        self, question: str, model: str | None = None, think: bool = True,
    ) -> AsyncIterator[str]:
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
        user_prompt = USER_PROMPT_TEMPLATE.format(
            context=context,
            question=question,
        )

        # 4. Stream response from LLM
        async for chunk in self._ollama.generate_stream(
            user_prompt, system=SYSTEM_PROMPT, model=model, think=think,
        ):
            yield chunk

    async def query(self, question: str, model: str | None = None) -> dict:
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

        user_prompt = USER_PROMPT_TEMPLATE.format(
            context=context,
            question=question,
        )

        response = await self._ollama.generate(
            user_prompt, system=SYSTEM_PROMPT, model=model,
        )
        return {"response": response, "sources": sorted(sources)}

    def get_sources(self) -> list[str]:
        return self._vector_store.get_document_names()
