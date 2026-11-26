"""
RAG Retrieval Interface for ServiceDesk-AI.

Defines the clean retrieval contract with BM25 as the in-house implementation.
The agent orchestration and LangGraph workflow interact ONLY with this interface,
allowing custom retrievers to be registered without altering workflow logic.
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from pathlib import Path
import re
from pydantic import BaseModel, Field
from app.config import settings
from app.utils.logger import logger

# Import models from retrieval_models to break circular dependency
from app.services.rag.retrieval_models import (
    BaseRetriever,
    RetrievalResult,
    RetrievedChunk,
)

# Re-export for backward compatibility
__all__ = [
    "BaseRetriever",
    "RetrievalResult",
    "RetrievedChunk",
    "UnconfiguredRetriever",
    "SampleFAQRetriever",
    "register_custom_retriever",
    "get_retriever",
]


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


# Global retriever registry allowing custom retriever registration
_active_retriever: Optional[BaseRetriever] = None


def register_custom_retriever(retriever: Optional[BaseRetriever]):
    """
    Hook to register a custom retriever (e.g., vector database or alternative implementation).
    Example:
        from app.services.rag.retrieval_interface import register_custom_retriever
        register_custom_retriever(MyCustomRetriever())
    """
    global _active_retriever
    _active_retriever = retriever
    if retriever is not None:
        logger.info(f"Registered custom RAG retriever: {retriever.__class__.__name__}")
    else:
        logger.info("Reset custom RAG retriever to default (BM25)")


def get_retriever() -> BaseRetriever:
    """Return the active retriever: custom, BM25, or unconfigured fallback."""
    global _active_retriever
    if _active_retriever is not None:
        return _active_retriever

    if not settings.RAG_ENABLED:
        return UnconfiguredRetriever()

    # Use BM25Retriever (in-house implementation)
    # Import here to avoid circular import
    from app.services.nlp.retriever import BM25Retriever
    return BM25Retriever(index_path=settings.BM25_INDEX_PATH)
