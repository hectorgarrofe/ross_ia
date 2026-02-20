from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    response: str
    sources: list[str] = []


class DocumentInfo(BaseModel):
    filename: str
    format: str
    chunks: int


class HealthStatus(BaseModel):
    status: str
    ollama: bool
    ollama_model: str
    embedding_model: str
    documents_count: int
    chunks_count: int
