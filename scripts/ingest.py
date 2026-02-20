#!/usr/bin/env python3
"""
Ingesta de documentos RÖS'S al vector store.

Uso:
    python scripts/ingest.py              # Ingesta desde data/documents/
    python scripts/ingest.py --reset      # Borra el vector store y reingesta
    python scripts/ingest.py --dir /ruta  # Ingesta desde directorio específico
"""
import argparse
import asyncio
import sys
import time
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.services.document_service import DocumentService
from backend.services.vector_store import VectorStore


async def main():
    parser = argparse.ArgumentParser(description="Ingesta documentos RÖS'S")
    parser.add_argument("--dir", type=str, help="Directorio con documentos")
    parser.add_argument("--reset", action="store_true", help="Borra el vector store antes de ingestar")
    args = parser.parse_args()

    doc_service = DocumentService()
    directory = Path(args.dir) if args.dir else None

    # List available files
    files = doc_service.list_supported_files(directory)
    if not files:
        print("No se encontraron documentos soportados (PDF, DOCX, TXT).")
        print(f"Coloca tus documentos en: {directory or 'data/documents/'}")
        return

    print("=" * 50)
    print("  RÖS'S IA - Ingesta de Documentos")
    print("=" * 50)
    print(f"\nDocumentos encontrados: {len(files)}")
    for f in files:
        print(f"  - {f}")

    # Reset if requested
    if args.reset:
        print("\nReseteando vector store...")
        vector_store = VectorStore()
        vector_store.reset()

    # Ingest
    print("\nProcesando documentos...\n")
    start = time.time()
    stats = await doc_service.ingest_directory(directory)
    elapsed = time.time() - start

    # Report
    print(f"\n{'=' * 50}")
    print(f"  Resultado:")
    print(f"  - Ficheros procesados: {stats['files_processed']}")
    print(f"  - Chunks creados: {stats['total_chunks']}")
    print(f"  - Tiempo: {elapsed:.1f}s")
    if stats["errors"]:
        print(f"  - Errores: {len(stats['errors'])}")
        for err in stats["errors"]:
            print(f"    - {err['file']}: {err['error']}")
    print(f"{'=' * 50}")


if __name__ == "__main__":
    asyncio.run(main())
