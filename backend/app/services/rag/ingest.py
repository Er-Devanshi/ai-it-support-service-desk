"""
Knowledge base ingestion pipeline for ServiceDesk-AI RAG.

Can be run:
1. Programmatically via `ingest_knowledge_base()`
2. From CLI: `python -m app.services.rag.ingest`
3. Via Admin API endpoint `POST /api/rag/ingest`
"""

import sys
import argparse
from pathlib import Path
from typing import Dict, Any, Optional

from app.config import settings
from app.utils.logger import logger
from app.services.rag.document_loader import load_knowledge_base_dir
from app.services.rag.chunker import DocumentChunker
from app.services.rag.vector_store import get_vector_store, ChromaVectorStore
from app.services.rag.embeddings import BaseEmbeddingService, get_embedding_service


def ingest_knowledge_base(
    directory: Optional[Path] = None,
    reset: bool = False,
    embedding_service: Optional[BaseEmbeddingService] = None,
) -> Dict[str, Any]:
    """
    Ingest IT documents into the ChromaDB vector database.
    
    Args:
        directory: Directory containing .txt, .md, and .pdf documents (defaults to settings.KNOWLEDGE_BASE_DIR).
        reset: If True, clears existing vector collection before indexing.
        embedding_service: Optional custom embedding service.
        
    Returns:
        Summary dict containing document and chunk counts.
    """
    kb_dir = Path(directory or settings.KNOWLEDGE_BASE_DIR)
    logger.info(f"Starting knowledge base ingestion from: {kb_dir} (reset={reset})")

    # 1. Load documents
    docs = load_knowledge_base_dir(kb_dir)
    if not docs:
        logger.warning(f"No documents found to ingest in {kb_dir}")
        return {
            "status": "warning",
            "message": f"No supported documents (.txt, .md, .pdf) found in {kb_dir}",
            "documents_loaded": 0,
            "chunks_indexed": 0,
        }

    # 2. Chunk documents
    chunker = DocumentChunker()
    all_chunks = []
    for doc in docs:
        chunks = chunker.chunk_document(doc)
        all_chunks.extend(chunks)

    logger.info(f"Generated {len(all_chunks)} chunk(s) from {len(docs)} document(s)")

    # 3. Store in ChromaDB
    emb_service = embedding_service or get_embedding_service()
    store = get_vector_store(embedding_service=emb_service)

    if reset:
        store.reset()

    indexed_count = store.add_chunks(all_chunks)

    result = {
        "status": "success",
        "documents_loaded": len(docs),
        "chunks_indexed": indexed_count,
        "total_in_db": store.count(),
        "persist_dir": str(store.persist_dir),
        "collection_name": store.collection_name,
        "embedding_model": emb_service.model_name,
    }
    logger.info(f"Ingestion complete: {result}")
    return result


def main():
    """CLI entrypoint for knowledge base ingestion."""
    parser = argparse.ArgumentParser(description="Ingest IT support documentation into ChromaDB for ServiceDesk-AI RAG.")
    parser.add_argument("--dir", type=str, default=None, help="Path to knowledge base directory")
    parser.add_argument("--reset", action="store_true", help="Clear existing vectors before indexing")
    parser.add_argument("--mock-embeddings", action="store_true", help="Use deterministic mock embeddings for offline testing")
    args = parser.parse_args()

    custom_emb = get_embedding_service(force_mock=True) if args.mock_embeddings else None
    input_dir = Path(args.dir) if args.dir else None

    print("=" * 60)
    print("ServiceDesk-AI — Knowledge Base Ingestion")
    print("=" * 60)

    try:
        res = ingest_knowledge_base(
            directory=input_dir,
            reset=args.reset,
            embedding_service=custom_emb,
        )
        print(f"Status:            {res['status']}")
        print(f"Documents Loaded:  {res['documents_loaded']}")
        print(f"Chunks Indexed:    {res['chunks_indexed']}")
        print(f"Total in Database: {res.get('total_in_db', 0)}")
        print(f"Persist Directory: {res.get('persist_dir', 'N/A')}")
        print(f"Embedding Model:   {res.get('embedding_model', 'N/A')}")
        print("=" * 60)
    except Exception as e:
        print(f"Ingestion failed: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
