import hashlib
from datetime import datetime, timezone
from pathlib import Path

from langchain_community.document_loaders import (
    PyPDFLoader,
    TextLoader,
)
from langchain_text_splitters import RecursiveCharacterTextSplitter

from config.settings import get_settings
from backend.services.vector_store import VectorStore

# docx2txt loader imported conditionally
try:
    from langchain_community.document_loaders import Docx2txtLoader
    HAS_DOCX = True
except ImportError:
    HAS_DOCX = False


SUPPORTED_EXTENSIONS = {".pdf", ".txt", ".docx", ".doc"}


def _get_loader(file_path: Path):
    ext = file_path.suffix.lower()
    if ext == ".pdf":
        return PyPDFLoader(str(file_path))
    if ext == ".txt":
        return TextLoader(str(file_path), encoding="utf-8")
    if ext in (".docx", ".doc"):
        if not HAS_DOCX:
            raise ImportError("docx2txt no instalado. Ejecuta: pip install docx2txt")
        return Docx2txtLoader(str(file_path))
    raise ValueError(f"Formato no soportado: {ext}")


def _chunk_id(source: str, chunk_index: int) -> str:
    content = f"{source}:{chunk_index}"
    return hashlib.md5(content.encode()).hexdigest()


class DocumentService:
    def __init__(self):
        settings = get_settings()
        self._splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""],
        )
        self._vector_store = VectorStore()

    async def ingest_file(self, file_path: Path) -> int:
        """Ingest a single file. Returns number of chunks created."""
        loader = _get_loader(file_path)
        documents = loader.load()

        chunks = self._splitter.split_documents(documents)

        if not chunks:
            return 0

        texts = []
        metadatas = []
        ids = []
        timestamp = datetime.now(timezone.utc).isoformat()

        for i, chunk in enumerate(chunks):
            texts.append(chunk.page_content)
            metadatas.append({
                "source": file_path.name,
                "format": file_path.suffix.lower(),
                "page": chunk.metadata.get("page", 0),
                "chunk_index": i,
                "ingested_at": timestamp,
            })
            ids.append(_chunk_id(file_path.name, i))

        await self._vector_store.add_documents(texts, metadatas, ids)
        return len(texts)

    async def ingest_directory(self, directory: Path | None = None) -> dict:
        """Ingest all supported files from a directory. Returns stats."""
        settings = get_settings()
        directory = directory or settings.documents_path

        stats = {"files_processed": 0, "total_chunks": 0, "errors": []}

        for file_path in sorted(directory.iterdir()):
            if file_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
                continue
            if file_path.name.startswith("."):
                continue

            try:
                num_chunks = await self.ingest_file(file_path)
                stats["files_processed"] += 1
                stats["total_chunks"] += num_chunks
                print(f"  {file_path.name}: {num_chunks} chunks")
            except Exception as e:
                stats["errors"].append({"file": file_path.name, "error": str(e)})
                print(f"  {file_path.name}: ERROR - {e}")

        return stats

    def list_supported_files(self, directory: Path | None = None) -> list[str]:
        settings = get_settings()
        directory = directory or settings.documents_path
        return [
            f.name
            for f in sorted(directory.iterdir())
            if f.suffix.lower() in SUPPORTED_EXTENSIONS and not f.name.startswith(".")
        ]
