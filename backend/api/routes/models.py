import httpx
from fastapi import APIRouter

from backend.services.ollama_client import OllamaClient
from config.settings import get_settings

router = APIRouter()

EMBEDDING_MODELS = {"bge-m3", "nomic-embed-text", "all-minilm", "mxbai-embed-large"}


@router.get("/models")
async def list_models():
    """List available LLM models from Ollama (excluding embedding models)."""
    settings = get_settings()
    ollama = OllamaClient()
    all_models = await ollama.list_models()

    llm_models = [
        m for m in all_models
        if not any(m["name"].startswith(emb) for emb in EMBEDDING_MODELS)
    ]

    return {
        "models": llm_models,
        "default": settings.llm_model,
    }


@router.post("/models/warmup")
async def warmup_model(request: dict):
    """Pre-load a model into Ollama memory."""
    model = request.get("model")
    if not model:
        return {"ok": False}
    ollama = OllamaClient()
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{ollama.base_url}/api/chat",
                json={
                    "model": model,
                    "messages": [],
                    "keep_alive": "30m",
                },
                timeout=60.0,
            )
            resp.raise_for_status()
        return {"ok": True}
    except Exception:
        return {"ok": False}
