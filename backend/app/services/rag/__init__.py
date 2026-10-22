"""
RAG (Retrieval-Augmented Generation) package for ServiceDesk-AI.
Exposes clean interfaces for document ingestion, chunking, embeddings,
ChromaDB vector store, and semantic retrieval.
"""

from app.services.rag.retrieval_interface import (
    BaseRetriever,
    RetrievedChunk,
    RetrievalResult,
    SampleFAQRetriever,
    UnconfiguredRetriever,
    ChromaDBRetriever,
    get_retriever,
    register_custom_retriever,
)
from app.services.rag.document_loader import (
    LoadedDocument,
    load_file,
    load_knowledge_base_dir,
)
from app.services.rag.chunker import DocumentChunker
from app.services.rag.embeddings import (
    BaseEmbeddingService,
    LocalSentenceTransformerEmbedding,
    MockEmbeddingService,
    get_embedding_service,
)
from app.services.rag.vector_store import (
    ChromaVectorStore,
    get_vector_store,
)

__all__ = [
    "BaseRetriever",
    "RetrievedChunk",
    "RetrievalResult",
    "SampleFAQRetriever",
    "UnconfiguredRetriever",
    "ChromaDBRetriever",
    "get_retriever",
    "register_custom_retriever",
    "LoadedDocument",
    "load_file",
    "load_knowledge_base_dir",
    "DocumentChunker",
    "BaseEmbeddingService",
    "LocalSentenceTransformerEmbedding",
    "MockEmbeddingService",
    "get_embedding_service",
    "ChromaVectorStore",
    "get_vector_store",
]
