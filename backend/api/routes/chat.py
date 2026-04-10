import json

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from backend.models.schemas import ChatRequest, ChatResponse
from backend.services.rag_service import RAGService

router = APIRouter()


@router.post("/chat")
async def chat(request: ChatRequest):
    """Chat endpoint with SSE streaming."""
    rag = RAGService()

    async def event_stream():
        try:
            async for chunk in rag.query_stream(request.message, model=request.model, think=request.think):
                data = json.dumps(chunk, ensure_ascii=False)
                yield f"data: {data}\n\n"
            yield f"data: {json.dumps({'done': True})}\n\n"
        except Exception as e:
            error_data = json.dumps({"error": str(e)}, ensure_ascii=False)
            yield f"data: {error_data}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/chat/sync", response_model=ChatResponse)
async def chat_sync(request: ChatRequest):
    """Non-streaming chat endpoint for testing."""
    rag = RAGService()
    result = await rag.query(request.message, model=request.model)
    return ChatResponse(
        response=result["response"],
        sources=result["sources"],
    )
