"""
Knowledge base ingestion pipeline for ServiceDesk-AI RAG using BM25.

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
from app.services.nlp.retriever import BM25Retriever


def ingest_knowledge_base(
    directory: Optional[Path] = None,
    reset: bool = False,
) -> Dict[str, Any]:
    """
    Ingest IT documents into the BM25 index.
    
    Args:
        directory: Directory containing .txt, .md, and .pdf documents (defaults to settings.KNOWLEDGE_BASE_DIR).
        reset: If True, rebuilds the entire index (not used with BM25 but kept for API compatibility).
        
    Returns:
        Summary dict containing document and chunk counts.
    """
    kb_dir = Path(directory or settings.KNOWLEDGE_BASE_DIR)
    logger.info(f"Starting knowledge base ingestion from: {kb_dir}")

    # 1. Load documents
    docs = load_knowledge_base_dir(kb_dir)
    if not docs:
        logger.warning(f"No documents found to ingest in {kb_dir}")
        return {
            "status": "warning",
            "message": f"No supported documents (.txt, .md, .pdf) found in {kb_dir}",
            "documents_loaded": 0,
            "chunks_indexed": 0,
            "total_in_db": 0,
            "index_dir": str(kb_dir.parent / "index"),
            "retriever_type": "BM25",
            "info": "No documents to index",
        }

    # 2. Chunk documents
    chunker = DocumentChunker()
    all_chunks = []
    for doc in docs:
        chunks = chunker.chunk_document(doc)
        all_chunks.extend(chunks)

    logger.info(f"Generated {len(all_chunks)} chunk(s) from {len(docs)} document(s)")

    # 3. Build BM25 index
    retriever = BM25Retriever()
    retriever.rebuild_from_documents([
        {
            "id": chunk.id,
            "title": chunk.document_title,
            "content": chunk.text,
            "source": chunk.source,
            "metadata": {
                "chunk_number": chunk.chunk_number,
                "document_id": chunk.document_id,
            },
        }
        for chunk in all_chunks
    ])

    index_dir = settings.KNOWLEDGE_BASE_DIR.parent / "index"
    result = {
        "status": "success",
        "documents_loaded": len(docs),
        "chunks_indexed": len(all_chunks),
        "total_in_db": len(all_chunks),
        "index_dir": str(index_dir),
        "retriever_type": "BM25 (in-house)",
        "info": f"BM25 index built with {len(all_chunks)} chunks from {len(docs)} documents",
    }
    logger.info(f"Ingestion complete: {result}")
    return result


def main():
    """CLI entrypoint for knowledge base ingestion."""
    parser = argparse.ArgumentParser(description="Ingest IT support documentation into BM25 index for ServiceDesk-AI RAG.")
    parser.add_argument("--dir", type=str, default=None, help="Path to knowledge base directory")
    parser.add_argument("--reset", action="store_true", help="Rebuild index (BM25 always rebuilds)")
    args = parser.parse_args()

    input_dir = Path(args.dir) if args.dir else None

    print("=" * 60)
    print("ServiceDesk-AI — Knowledge Base Ingestion (BM25)")
    print("=" * 60)

    try:
        res = ingest_knowledge_base(
            directory=input_dir,
            reset=args.reset,
        )
        print(f"Status:            {res['status']}")
        print(f"Documents Loaded:  {res['documents_loaded']}")
        print(f"Chunks Indexed:    {res['chunks_indexed']}")
        print(f"Total in Index:    {res.get('total_in_db', 0)}")
        print(f"Index Directory:   {res.get('index_dir', 'N/A')}")
        print(f"Retriever Type:    {res.get('retriever_type', 'N/A')}")
        print("=" * 60)
    except Exception as e:
        print(f"Ingestion failed: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
