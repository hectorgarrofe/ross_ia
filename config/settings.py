from pathlib import Path
from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Ollama
    ollama_base_url: str = "http://localhost:11434"
    llm_model: str = "qwen2.5:7b"
    embedding_model: str = "bge-m3"

    # RAG
    chunk_size: int = 512
    chunk_overlap: int = 50
    retrieval_top_k: int = 5

    # Paths
    documents_dir: str = "./data/documents"
    vectorstore_dir: str = "./data/vectorstore"

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    model_config = {
        "env_prefix": "ROSS_",
        "env_file": ".env",
        "env_file_encoding": "utf-8",
    }

    @property
    def documents_path(self) -> Path:
        return Path(self.documents_dir)

    @property
    def vectorstore_path(self) -> Path:
        return Path(self.vectorstore_dir)


@lru_cache
def get_settings() -> Settings:
    return Settings()
