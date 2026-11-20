"""
RAG Retrieval Data Models.

This module contains ONLY the data model definitions and abstract base class
for the retrieval interface. It does NOT import from app.services.nlp or 
app.services.rag.retrieval_interface to avoid circular imports.
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


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
