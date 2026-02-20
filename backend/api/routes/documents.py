import shutil
from pathlib import Path

from fastapi import APIRouter, UploadFile, File

from backend.models.schemas import DocumentInfo
from backend.services.document_service import DocumentService, SUPPORTED_EXTENSIONS
from backend.services.vector_store import VectorStore
from config.settings import get_settings

router = APIRouter()


@router.get("/documents", response_model=list[DocumentInfo])
async def list_documents():
    """List all ingested documents."""
    vector_store = VectorStore()
    doc_service = DocumentService()
    settings = get_settings()

    documents = []
    for name in vector_store.get_document_names():
        # Count chunks for this document
        all_data = vector_store._collection.get(
            where={"source": name},
            include=["metadatas"],
        )
        documents.append(DocumentInfo(
            filename=name,
            format=Path(name).suffix.lower(),
            chunks=len(all_data["metadatas"]),
        ))
    return documents


@router.post("/documents/upload")
async def upload_document(file: UploadFile = File(...)):
    """Upload and ingest a document."""
    ext = Path(file.filename).suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        return {
            "error": f"Formato no soportado: {ext}. Usa: {', '.join(SUPPORTED_EXTENSIONS)}"
        }

    settings = get_settings()
    dest = Path(settings.documents_dir) / file.filename

    # Save file
    with open(dest, "wb") as f:
        shutil.copyfileobj(file.file, f)

    # Ingest
    doc_service = DocumentService()
    num_chunks = await doc_service.ingest_file(dest)

    return {
        "filename": file.filename,
        "chunks": num_chunks,
        "message": f"Documento procesado: {num_chunks} chunks creados",
    }
