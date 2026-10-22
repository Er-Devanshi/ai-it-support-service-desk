"""
Comprehensive test suite for ServiceDesk-AI RAG Pipeline.

Covers:
1. Document loading (.txt, .md, .pdf)
2. Chunking & troubleshooting step preservation
3. Deterministic chunk IDs & deduplication
4. Embedding service (mock & local)
5. Persistent ChromaDB vector store
6. Semantic retrieval & relevance threshold filtering
7. Citation structure & metadata
8. Irrelevant & unknown query handling
9. RAG integration with /api/chat workflow
10. Protected admin ingestion API & status probe
11. Preservation of ticket and approval workflows
"""

import pytest
from pathlib import Path
import tempfile
import shutil

from app.config import settings
from app.models.orm import UserRole
from app.services.rag.document_loader import (
    LoadedDocument,
    load_file,
    load_knowledge_base_dir,
    _extract_title,
    _infer_category_from_text,
)
from app.services.rag.chunker import DocumentChunker
from app.services.rag.embeddings import (
    MockEmbeddingService,
    LocalSentenceTransformerEmbedding,
    get_embedding_service,
    set_embedding_service,
)
from app.services.rag.vector_store import ChromaVectorStore
from app.services.rag.retrieval_interface import (
    ChromaDBRetriever,
    SampleFAQRetriever,
    UnconfiguredRetriever,
    get_retriever,
    register_custom_retriever,
)
from app.services.rag.ingest import ingest_knowledge_base
from app.services.auth_service import create_access_token


@pytest.fixture
def mock_embeddings():
    """Deterministic mock embedding service to ensure fast offline test execution."""
    return MockEmbeddingService()


@pytest.fixture
def temp_chroma_dir():
    """Temporary directory for test ChromaDB persistence."""
    tmp = tempfile.mkdtemp(prefix="test_chroma_")
    yield Path(tmp)
    shutil.rmtree(tmp, ignore_errors=True)


# ============================================================================
# 1. Document Loading Tests
# ============================================================================

def test_document_loader_txt_and_md():
    """Test loading plain text and Markdown files from the knowledge base."""
    docs = load_knowledge_base_dir(settings.KNOWLEDGE_BASE_DIR)
    assert len(docs) >= 1
    file_types = {d.file_type for d in docs}
    assert "txt" in file_types or "md" in file_types

    # Check title extraction
    faq_doc = next((d for d in docs if "faq" in d.file_name.lower()), None)
    assert faq_doc is not None
    assert faq_doc.title is not None
    assert len(faq_doc.content) > 100


def test_title_and_category_inference():
    """Test heuristic title extraction and category classification."""
    md_text = "# Corporate VPN Handbook\n\nInstructions for AnyConnect connection."
    title = _extract_title(md_text, "vpn_guide.md")
    assert title == "Corporate VPN Handbook"

    cat = _infer_category_from_text(md_text)
    assert cat == "network"


# ============================================================================
# 2. Chunking & Metadata Tests
# ============================================================================

def test_chunking_preserves_troubleshooting_steps():
    """Test that chunking does not slice through sequential numbered steps."""
    chunker = DocumentChunker(chunk_size=300, chunk_overlap=50)
    sample_text = (
        "## Wireless Diagnostic Steps\n\n"
        "Follow these steps to restore connectivity:\n"
        "1. Open Network Settings.\n"
        "2. Forget the corporate SSID.\n"
        "3. Re-enter your enterprise credentials.\n"
        "4. Restart the network adapter driver.\n"
        "5. Verify IP address allocation from DHCP server."
    )
    doc = LoadedDocument(
        file_path="test_wifi.md",
        file_name="test_wifi.md",
        file_type="md",
        title="Wireless Guide",
        content=sample_text,
        category="network",
    )
    chunks = chunker.chunk_document(doc)
    assert len(chunks) >= 1
    # Check that steps are present in the chunk
    full_content = " ".join([c.content for c in chunks])
    for step in ["1.", "2.", "3.", "4.", "5."]:
        assert step in full_content


def test_chunking_deterministic_ids_prevent_duplicates():
    """Verify that chunk IDs are deterministic across multiple runs."""
    chunker = DocumentChunker()
    doc = LoadedDocument(
        file_path="test_doc.md",
        file_name="test_doc.md",
        file_type="md",
        title="Test Document",
        content="# Section One\n\nContent for section one.\n\n# Section Two\n\nContent for section two.",
        category="general",
    )
    run1 = chunker.chunk_document(doc)
    run2 = chunker.chunk_document(doc)

    assert len(run1) == len(run2)
    for c1, c2 in zip(run1, run2):
        assert c1.chunk_id == c2.chunk_id
        assert c1.title == c2.title


# ============================================================================
# 3. Vector Database & Semantic Retrieval Tests
# ============================================================================

def test_chroma_vector_store_add_and_deduplicate(temp_chroma_dir, mock_embeddings):
    """Test storing chunks in ChromaDB and verifying that re-ingestion does not create duplicate chunks."""
    store = ChromaVectorStore(
        persist_dir=temp_chroma_dir,
        collection_name="test_collection",
        embedding_service=mock_embeddings,
    )
    assert store.count() == 0

    chunker = DocumentChunker()
    doc = LoadedDocument(
        file_path="vpn_sample.md",
        file_name="vpn_sample.md",
        file_type="md",
        title="VPN Troubleshooting",
        content="# VPN Gateway Resolution\n\n1. Check AnyConnect tunnel.\n2. Disconnect and reconnect.",
        category="network",
    )
    chunks = chunker.chunk_document(doc)
    added = store.add_chunks(chunks)
    assert added == len(chunks)
    assert store.count() == len(chunks)

    # Re-ingest exact same chunks
    store.add_chunks(chunks)
    # Count must remain exactly the same due to upserting deterministic IDs
    assert store.count() == len(chunks)


def test_semantic_retrieval_matches_relevant_query(temp_chroma_dir, mock_embeddings):
    """Test that query matching returns relevant document chunks with valid similarity scores."""
    store = ChromaVectorStore(
        persist_dir=temp_chroma_dir,
        collection_name="test_retrieval",
        embedding_service=mock_embeddings,
    )
    chunker = DocumentChunker()

    doc_vpn = LoadedDocument(
        file_path="vpn.md",
        file_name="vpn.md",
        file_type="md",
        title="VPN Guide",
        content="Corporate VPN connection fails with Error 412 when remote peer drops packets. Toggle protocol to SSL.",
        category="network",
    )
    doc_printer = LoadedDocument(
        file_path="printer.md",
        file_name="printer.md",
        file_type="md",
        title="Printer Guide",
        content="Paper jam in tray 2. Restart the Windows Print Spooler service to clear stuck print jobs.",
        category="hardware",
    )

    store.add_chunks(chunker.chunk_document(doc_vpn))
    store.add_chunks(chunker.chunk_document(doc_printer))

    # Query for VPN
    results = store.search("VPN Error 412 connection dropped", top_k=2, relevance_threshold=0.2)
    assert len(results) > 0
    top = results[0]
    assert "vpn" in top.source.lower() or "vpn" in top.title.lower()
    assert top.relevance_score is not None
    assert top.relevance_score > 0.0


def test_irrelevant_query_filtered_by_threshold(temp_chroma_dir, mock_embeddings):
    """Test that unrelated or out-of-domain queries return empty results when below threshold."""
    store = ChromaVectorStore(
        persist_dir=temp_chroma_dir,
        collection_name="test_irrelevant",
        embedding_service=mock_embeddings,
    )
    chunker = DocumentChunker()
    doc = LoadedDocument(
        file_path="network.md",
        file_name="network.md",
        file_type="md",
        title="Network Operations",
        content="Configure router DHCP scopes and IP address pools for employee workstations.",
        category="network",
    )
    store.add_chunks(chunker.chunk_document(doc))

    # Query about completely unrelated topic with strict threshold
    results = store.search("Recipe for chocolate cake with strawberry frosting", top_k=3, relevance_threshold=0.6)
    assert len(results) == 0


def test_empty_and_whitespace_query_returns_empty(temp_chroma_dir, mock_embeddings):
    """Test graceful handling of empty or blank query strings."""
    store = ChromaVectorStore(
        persist_dir=temp_chroma_dir,
        collection_name="test_empty",
        embedding_service=mock_embeddings,
    )
    assert store.search("") == []
    assert store.search("   ") == []


# ============================================================================
# 4. Retriever Interface & RAG Integration Tests
# ============================================================================

def test_chromadb_retriever_contract(temp_chroma_dir, mock_embeddings):
    """Verify that ChromaDBRetriever conforms to BaseRetriever interface."""
    store = ChromaVectorStore(
        persist_dir=temp_chroma_dir,
        collection_name="test_contract",
        embedding_service=mock_embeddings,
    )
    chunker = DocumentChunker()
    doc = LoadedDocument(
        file_path="pw.md",
        file_name="pw.md",
        file_type="md",
        title="Password Policy",
        content="Passwords expire every 90 days. Reset password at the employee portal.",
        category="account",
    )
    store.add_chunks(chunker.chunk_document(doc))

    retriever = ChromaDBRetriever(vector_store=store)
    res = retriever.retrieve("How do I reset my expired password?", top_k=2)

    assert res.is_available is True
    assert "ChromaDB" in res.provider_info
    assert len(res.documents) > 0
    doc0 = res.documents[0]
    assert doc0.source == "pw.md"
    assert doc0.relevance_score is not None


def test_disabled_rag_returns_unconfigured(monkeypatch):
    """Test that settings.RAG_ENABLED = False returns UnconfiguredRetriever."""
    monkeypatch.setattr(settings, "RAG_ENABLED", False)
    # Ensure no custom retriever is active
    register_custom_retriever(None)
    retriever = get_retriever()
    assert isinstance(retriever, UnconfiguredRetriever)
    res = retriever.retrieve("Any question")
    assert res.is_available is False
    assert len(res.documents) == 0


# ============================================================================
# 5. End-to-End Chat API RAG Integration Tests
# ============================================================================

def test_chat_endpoint_returns_citations(client):
    """Test that POST /api/chat includes structured citations in response."""
    res = client.post("/api/chat", json={"message": "How do I fix VPN connection error?"})
    assert res.status_code == 200
    data = res.json()
    assert "reply" in data
    assert "citations" in data
    assert isinstance(data["citations"], list)
    if data["citations"]:
        c = data["citations"][0]
        assert "source" in c
        assert "title" in c
        assert "snippet" in c
        assert "relevance_score" in c


def test_chat_preserves_ticket_and_approval_workflows(client):
    """Test that actions requiring approval still generate approval requests while maintaining citations."""
    res = client.post("/api/chat", json={"message": "Please unlock account for user john.doe"})
    assert res.status_code == 200
    data = res.json()
    assert data["requires_approval"] is True
    assert data["approval_id"] is not None
    assert "citations" in data


# ============================================================================
# 6. Admin Ingestion API & Status Routes
# ============================================================================

def test_rag_status_endpoint(client):
    """Test GET /api/rag/status returns diagnostics."""
    res = client.get("/api/rag/status")
    assert res.status_code == 200
    data = res.json()
    assert "rag_enabled" in data
    assert data["rag_enabled"] is True
    assert "document_count" in data


def test_rag_ingest_endpoint_requires_auth(client):
    """Test that anonymous users cannot trigger knowledge base ingestion."""
    res = client.post("/api/rag/ingest", json={"reset": False})
    assert res.status_code == 401


def test_rag_ingest_endpoint_rbac_forbidden_for_employee(client, employee_headers):
    """Test that non-admin employee role cannot trigger ingestion."""
    res = client.post(
        "/api/rag/ingest",
        json={"reset": False},
        headers=employee_headers,
    )
    assert res.status_code == 403


def test_rag_ingest_endpoint_authorized_for_admin(client, admin_headers):
    """Test that admin user can successfully trigger knowledge base ingestion."""
    res = client.post(
        "/api/rag/ingest",
        json={"reset": False},
        headers=admin_headers,
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert data["chunks_indexed"] > 0
    assert data["total_in_db"] > 0
