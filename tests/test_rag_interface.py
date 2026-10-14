"""
Tests for RAG Retrieval Interface Contract (Sanskriti Agarwal boundary).
Verifies unconfigured vs configured behavior and custom retriever registration hook.
"""

from app.services.rag.retrieval_interface import (
    BaseRetriever,
    RetrievalResult,
    RetrievedChunk,
    UnconfiguredRetriever,
    SampleFAQRetriever,
    get_retriever,
    register_custom_retriever,
)
from app.config import settings


def test_unconfigured_retriever_returns_unavailable():
    """Test 17a: When unconfigured, returns is_available=False with descriptive message."""
    retriever = UnconfiguredRetriever()
    res = retriever.retrieve("How do I connect to VPN?")
    assert res.is_available is False
    assert len(res.documents) == 0
    assert "Awaiting Sanskriti" in res.provider_info


def test_sample_faq_retriever_finds_relevant_chunks():
    """Test 17b: Sample reference retriever matches knowledge base and provides source metadata."""
    retriever = SampleFAQRetriever()
    res = retriever.retrieve("Wi-Fi network is not working")
    assert res.is_available is True
    assert len(res.documents) > 0
    top = res.documents[0]
    assert "Wi-Fi" in top.title or "Network" in top.title
    assert top.source.endswith(".txt")
    assert top.relevance_score is not None
    assert top.relevance_score > 0.0


def test_custom_retriever_registration_hook():
    """Test 17c: Hook allows Sanskriti to register external vector store seamlessly."""
    class MockChromaDBRetriever(BaseRetriever):
        def retrieve(self, query: str, context=None, top_k=3):
            return RetrievalResult(
                query=query,
                documents=[
                    RetrievedChunk(
                        chunk_id="chroma-001",
                        source="vector_store/chroma",
                        title="Vector Search Result",
                        content="Sample embedded passage content.",
                        relevance_score=0.95,
                    )
                ],
                is_available=True,
                provider_info="CustomChromaDBRetriever",
            )

    register_custom_retriever(MockChromaDBRetriever())
    active = get_retriever()
    assert isinstance(active, MockChromaDBRetriever)

    result = active.retrieve("test query")
    assert result.provider_info == "CustomChromaDBRetriever"
    assert result.documents[0].chunk_id == "chroma-001"

    # Reset retriever registry back to default
    register_custom_retriever(None)
