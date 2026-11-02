"""
BM25-based retriever compatible with the retrieval_interface contract.

Implements BaseRetriever from services/rag/retrieval_interface.py
using our own BM25 implementation instead of ChromaDB/embeddings.

Returns RetrievedChunk objects in the exact format expected by the workflow.
"""

import json
from typing import Optional, List
from pathlib import Path

from app.services.rag.retrieval_interface import BaseRetriever, RetrievalResult, RetrievedChunk
from app.services.nlp.bm25 import BM25Index
from app.config import settings
from app.utils.logger import logger


class BM25Retriever(BaseRetriever):
    """BM25-based retriever with in-memory index persisted to JSON."""

    def __init__(self, index_path: Optional[Path] = None):
        """
        Initialize retriever.
        
        Args:
            index_path: Path to saved BM25 index. If None, uses default.
        """
        self.index_path = index_path or (settings.KNOWLEDGE_BASE_DIR.parent / "index" / "bm25_index.json")
        self.index = None
        self._load_index()

    def _load_index(self):
        """Load index from disk if it exists, otherwise create empty."""
        if self.index_path.exists():
            try:
                self.index = BM25Index.load(self.index_path)
                logger.info(f"BM25 index loaded: {self.index.total_docs} docs")
            except Exception as e:
                logger.warning(f"Failed to load BM25 index: {e}, creating fresh index")
                self.index = BM25Index()
        else:
            self.index = BM25Index()

    def retrieve(
        self,
        query: str,
        context: Optional[str] = None,
        top_k: int = 3,
    ) -> RetrievalResult:
        """
        Retrieve relevant knowledge chunks using BM25.
        
        Returns RetrievalResult with RetrievedChunk objects in standard format.
        """
        if not query or not query.strip():
            return RetrievalResult(
                query=query,
                documents=[],
                is_available=True,
                provider_info="BM25Retriever (In-house)",
            )

        if self.index.total_docs == 0:
            return RetrievalResult(
                query=query,
                documents=[],
                is_available=False,
                provider_info="BM25Retriever (No documents indexed)",
                error_message="Knowledge base index is empty",
            )

        try:
            # Query expansion: prepend recent context if available
            augmented_query = query
            if context and len(context.strip()) > 0:
                recent_turns = [line.strip() for line in context.strip().split("\n") if line.strip()]
                if recent_turns:
                    augmented_query = f"{recent_turns[-1]} {query}"

            # Search
            ranked_results = self.index.search(augmented_query, top_k=top_k)

            # Convert to RetrievedChunk objects
            chunks = []
            for doc_id, score in ranked_results:
                # Normalize score to [0.0, 1.0] for consistency
                # BM25 scores are typically 0 to ~10, normalize via sigmoid-like approach
                normalized_score = min(1.0, score / 10.0)

                if normalized_score < settings.RAG_RELEVANCE_THRESHOLD:
                    continue  # Skip below threshold

                doc = self.index.documents[doc_id]
                chunk = RetrievedChunk(
                    chunk_id=doc_id,
                    source=doc["source"],
                    title=doc["title"],
                    content=doc["content"],
                    relevance_score=round(normalized_score, 3),
                    metadata=doc.get("metadata", {}),
                )
                chunks.append(chunk)

            return RetrievalResult(
                query=query,
                documents=chunks,
                is_available=True,
                provider_info="BM25Retriever (In-house)",
            )

        except Exception as e:
            logger.error(f"BM25 retrieval error: {e}")
            return RetrievalResult(
                query=query,
                documents=[],
                is_available=False,
                provider_info="BM25Retriever",
                error_message=str(e),
            )

    def rebuild_from_documents(self, documents: List[dict]) -> None:
        """
        Rebuild index from a list of document dicts.
        
        Each document dict should have: id, title, content, source, metadata (optional)
        """
        self.index = BM25Index()
        for doc in documents:
            self.index.add_document(
                doc_id=doc["id"],
                title=doc.get("title", ""),
                content=doc.get("content", ""),
                source=doc.get("source", ""),
                metadata=doc.get("metadata", {}),
            )
        self.index.finalize()
        self.save_index()
        logger.info(f"BM25 index rebuilt with {len(documents)} documents")

    def save_index(self) -> None:
        """Save current index to disk."""
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        self.index.save(self.index_path)

    def add_document(self, doc_id: str, title: str, content: str, source: str, metadata: Optional[dict] = None) -> None:
        """Add a single document to the index."""
        self.index.add_document(doc_id, title, content, source, metadata)
        self.save_index()
