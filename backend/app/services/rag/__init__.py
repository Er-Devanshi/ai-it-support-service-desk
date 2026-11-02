"""
RAG (Retrieval-Augmented Generation) package for ServiceDesk-AI.

Updated for in-house NLP engine:
- BM25 retrieval (no embeddings, no vector DB)
- Document ingestion and chunking
- Exposes clean interfaces for plug-in compatibility
"""

from app.services.rag.retrieval_interface import (
    BaseRetriever,
    RetrievedChunk,
    RetrievalResult,
    SampleFAQRetriever,
    UnconfiguredRetriever,
    get_retriever,
    register_custom_retriever,
)
from app.services.rag.document_loader import (
    LoadedDocument,
    load_file,
    load_knowledge_base_dir,
)
from app.services.rag.chunker import DocumentChunker

__all__ = [
    "BaseRetriever",
    "RetrievedChunk",
    "RetrievalResult",
    "SampleFAQRetriever",
    "UnconfiguredRetriever",
    "get_retriever",
    "register_custom_retriever",
    "LoadedDocument",
    "load_file",
    "load_knowledge_base_dir",
    "DocumentChunker",
]
