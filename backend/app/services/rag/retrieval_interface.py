"""
RAG Retrieval Interface Contract for ServiceDesk-AI.

================================================================================
TEAM BOUNDARY NOTICE:
This module defines the clean retrieval contract for Sanskriti Agarwal.
The agent orchestration and LangGraph workflow interact ONLY with this interface,
ensuring that ChromaDB, FAISS, or any other vector database can be plugged in
without altering agent orchestration, API routes, or backend security logic.
================================================================================
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from pathlib import Path
import re
from pydantic import BaseModel, Field
from app.config import settings
from app.utils.logger import logger


class RetrievedChunk(BaseModel):
    """A single retrieved document chunk with provenance metadata."""
    chunk_id: str = Field(description="Unique identifier for the chunk")
    source: str = Field(description="File path, URL, or document origin (e.g. 'sample_it_faq.txt')")
    title: str = Field(description="Title or heading of the document/section")
    content: str = Field(description="Text passage content")
    relevance_score: Optional[float] = Field(default=None, description="Similarity or relevance score [0.0 - 1.0]")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Arbitrary metadata (category, tags, etc.)")


class RetrievalResult(BaseModel):
    """Structured result returned by any retriever implementation."""
    query: str
    documents: List[RetrievedChunk] = Field(default_factory=list)
    is_available: bool = Field(description="True if retrieval service executed successfully, False if unconfigured/disabled")
    provider_info: str = Field(description="Name or descriptor of the retrieval backend (e.g., 'ChromaDB', 'SampleFAQ-Reader')")
    error_message: Optional[str] = None


class BaseRetriever(ABC):
    """Abstract retrieval contract."""

    @abstractmethod
    def retrieve(
        self,
        query: str,
        context: Optional[str] = None,
        top_k: int = 3,
    ) -> RetrievalResult:
        """
        Retrieve relevant knowledge chunks for a given query.
        
        Args:
            query: The user's IT problem statement.
            context: Optional conversation context or previous turns.
            top_k: Maximum number of relevant chunks to return.
        """
        pass


class UnconfiguredRetriever(BaseRetriever):
    """Explicit placeholder retriever when no knowledge base or vector DB is configured."""

    def retrieve(
        self,
        query: str,
        context: Optional[str] = None,
        top_k: int = 3,
    ) -> RetrievalResult:
        return RetrievalResult(
            query=query,
            documents=[],
            is_available=False,
            provider_info="Unconfigured (Awaiting Sanskriti's Vector DB implementation)",
            error_message="Retrieval pipeline is not currently configured or enabled.",
        )


class SampleFAQRetriever(BaseRetriever):
    """
    Reference keyword-based retriever that parses `data/knowledge_base/sample_it_faq.txt`.
    Provides realistic document chunks and verified citations for local demonstrations
    and testing before the vector database is indexed.
    """

    def __init__(self, faq_path: Optional[Path] = None):
        self.faq_path = faq_path or (settings.KNOWLEDGE_BASE_DIR / "sample_it_faq.txt")
        self._faqs: List[Dict[str, str]] = []
        self._load_faqs()

    def _load_faqs(self):
        """Parse FAQs from sample text file."""
        if not self.faq_path.exists():
            logger.warning(f"Knowledge base file not found at: {self.faq_path}")
            return

        try:
            content = self.faq_path.read_text(encoding="utf-8")
            # Split sections by FAQ delimiters
            sections = re.split(r"-{40,}\s*FAQ\s*(\d+)\s*[—–-]\s*(.*?)\s*-{40,}", content)
            
            # sections format: [preamble, faq_num1, title1, text1, faq_num2, title2, text2, ...]
            for i in range(1, len(sections), 3):
                if i + 2 < len(sections):
                    faq_num = sections[i].strip()
                    faq_title = sections[i + 1].strip()
                    faq_body = sections[i + 2].strip()
                    self._faqs.append({
                        "id": f"FAQ-{faq_num}",
                        "title": f"FAQ {faq_num}: {faq_title}",
                        "body": faq_body,
                        "source": self.faq_path.name,
                    })
        except Exception as e:
            logger.error(f"Failed to load sample knowledge base: {e}")

    def retrieve(
        self,
        query: str,
        context: Optional[str] = None,
        top_k: int = 3,
    ) -> RetrievalResult:
        if not self._faqs:
            return RetrievalResult(
                query=query,
                documents=[],
                is_available=False,
                provider_info="SampleFAQRetriever",
                error_message="No FAQs loaded from sample knowledge base.",
            )

        query_tokens = set(re.findall(r"\w+", query.lower()))
        scored_faqs = []

        for faq in self._faqs:
            faq_text = (faq["title"] + " " + faq["body"]).lower()
            faq_tokens = set(re.findall(r"\w+", faq_text))
            intersection = query_tokens.intersection(faq_tokens)
            if intersection:
                # Basic Jaccard-like keyword overlap score
                score = round(len(intersection) / max(len(query_tokens), 1), 2)
                scored_faqs.append((score, faq))

        scored_faqs.sort(key=lambda x: x[0], reverse=True)
        top_matches = scored_faqs[:top_k]

        chunks = []
        for score, faq in top_matches:
            chunks.append(
                RetrievedChunk(
                    chunk_id=faq["id"],
                    source=faq["source"],
                    title=faq["title"],
                    content=faq["body"],
                    relevance_score=score,
                    metadata={"source_file": str(self.faq_path)},
                )
            )

        return RetrievalResult(
            query=query,
            documents=chunks,
            is_available=True,
            provider_info="SampleFAQRetriever (Reference implementation)",
        )


class ChromaDBRetriever(BaseRetriever):
    """
    Production semantic retriever backed by ChromaDB vector database.
    Performs dense vector similarity matching and enforces relevance thresholds.
    """

    def __init__(self, vector_store=None):
        if vector_store is not None:
            self.vector_store = vector_store
        else:
            from app.services.rag.vector_store import get_vector_store
            self.vector_store = get_vector_store()

    def retrieve(
        self,
        query: str,
        context: Optional[str] = None,
        top_k: int = 3,
    ) -> RetrievalResult:
        if not query or not query.strip():
            return RetrievalResult(
                query=query,
                documents=[],
                is_available=True,
                provider_info=f"ChromaDB ({self.vector_store.embedding_service.model_name})",
            )

        # Prepend conversation context if present
        augmented_query = query
        if context and len(context.strip()) > 0:
            recent_turns = [line.strip() for line in context.strip().split("\n") if line.strip()]
            if recent_turns:
                augmented_query = f"{recent_turns[-1]} {query}"

        try:
            chunks = self.vector_store.search(
                query=augmented_query,
                top_k=top_k,
                relevance_threshold=settings.RAG_RELEVANCE_THRESHOLD,
            )
            return RetrievalResult(
                query=query,
                documents=chunks,
                is_available=True,
                provider_info=f"ChromaDB ({self.vector_store.embedding_service.model_name})",
            )
        except Exception as e:
            logger.error(f"ChromaDB retrieval error: {e}")
            return RetrievalResult(
                query=query,
                documents=[],
                is_available=False,
                provider_info="ChromaDB",
                error_message=str(e),
            )


# Global retriever registry allowing Sanskriti to register her vector database instance
_active_retriever: Optional[BaseRetriever] = None


def register_custom_retriever(retriever: Optional[BaseRetriever]):
    """
    Hook for Sanskriti to register her ChromaDB / FAISS retriever.
    Example:
        from app.services.rag.retrieval_interface import register_custom_retriever
        register_custom_retriever(MyChromaDBRetriever())
    """
    global _active_retriever
    _active_retriever = retriever
    if retriever is not None:
        logger.info(f"Registered custom RAG retriever: {retriever.__class__.__name__}")
    else:
        logger.info("Reset custom RAG retriever to default")


def get_retriever() -> BaseRetriever:
    """Return the active retriever (custom, ChromaDB, sample fallback, or unconfigured)."""
    global _active_retriever
    if _active_retriever is not None:
        return _active_retriever

    if not settings.RAG_ENABLED:
        return UnconfiguredRetriever()

    # Try ChromaDB if initialized and has documents
    try:
        from app.services.rag.vector_store import get_vector_store
        store = get_vector_store()
        if store.count() > 0:
            return ChromaDBRetriever(vector_store=store)
    except Exception as e:
        logger.debug(f"ChromaDB not ready or empty ({e}), using SampleFAQRetriever fallback")

    # Use the reference SampleFAQRetriever by default
    return SampleFAQRetriever()
