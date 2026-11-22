"""
BM25-based retriever compatible with the retrieval_interface contract.

Implements BaseRetriever from services/rag/retrieval_models.py
using our own BM25 implementation instead of ChromaDB/embeddings.

Returns RetrievedChunk objects in the exact format expected by the workflow.
"""

import json
from typing import Optional, List
from pathlib import Path

from app.services.rag.retrieval_models import BaseRetriever, RetrievalResult, RetrievedChunk
from app.services.nlp.bm25 import BM25Index
from app.config import settings
from app.utils.logger import logger


class BM25Retriever(BaseRetriever):
    """BM25-based retriever with in-memory index persisted to JSON."""

    def __init__(self, index_path: Optional[Path] = None):
        """
        Initialize retriever.
        
        Args:
            index_path: Path to saved BM25 index. If None, uses BM25_INDEX_PATH from config.
        """
        self.index_path = index_path or settings.BM25_INDEX_PATH
        self.index = None
        self.synonyms = {}
        self._load_synonyms()
        self._load_index()

    def _load_synonyms(self):
        """Load query synonyms from config file."""
        synonyms_path = settings.QUERY_SYNONYMS_PATH
        if synonyms_path.exists():
            try:
                with open(synonyms_path, "r") as f:
                    config = json.load(f)
                self.synonyms = config.get("synonyms", {})
                logger.info(f"Loaded {len(self.synonyms)} synonym groups from {synonyms_path}")
            except Exception as e:
                logger.warning(f"Failed to load synonyms from {synonyms_path}: {e}")
                self.synonyms = {}
        else:
            logger.warning(f"Synonyms file not found at {synonyms_path}")

    def _expand_query_with_synonyms(self, query: str) -> str:
        """
        Expand query with synonyms for better vocabulary matching.
        Only adds synonym terms for words that appear in the query,
        with lower weight to avoid noise. Original tokens are repeated
        to maintain their importance.
        """
        if not self.synonyms:
            return query
        
        # Tokenize query
        from app.services.nlp.tokenizer import tokenize
        tokens = tokenize(query, remove_stopwords=False, stem=False)
        
        # Keep original tokens (original weight)
        expanded_tokens = list(tokens)
        
        # For each token that has synonyms, add the synonym terms at reduced weight
        # (achieved by adding them once while originals stay)
        matched_synonyms = []
        for token in tokens:
            token_lower = token.lower()
            if token_lower in self.synonyms:
                # Add only the synonym group for this specific term
                matched_synonyms.extend(self.synonyms[token_lower])
        
        # Append synonyms once at the end (lower effective weight than original)
        if matched_synonyms:
            expanded_tokens.extend(matched_synonyms)
        
        return " ".join(expanded_tokens)

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
        Retrieve relevant knowledge chunks using BM25 with synonym expansion.
        
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
            
            # Expand query with synonyms for better vocabulary matching
            augmented_query = self._expand_query_with_synonyms(augmented_query)

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
