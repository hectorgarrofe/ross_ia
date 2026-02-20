from fastapi import APIRouter

from backend.models.schemas import HealthStatus
from backend.services.ollama_client import OllamaClient
from backend.services.vector_store import VectorStore
from config.settings import get_settings

router = APIRouter()


@router.get("/health", response_model=HealthStatus)
async def health_check():
    settings = get_settings()
    ollama = OllamaClient()
    vector_store = VectorStore()

    ollama_ok = await ollama.health_check()

    return HealthStatus(
        status="ok" if ollama_ok else "degraded",
        ollama=ollama_ok,
        ollama_model=settings.llm_model,
        embedding_model=settings.embedding_model,
        documents_count=len(vector_store.get_document_names()),
        chunks_count=vector_store.chunks_count,
    )
