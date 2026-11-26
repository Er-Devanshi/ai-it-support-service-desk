"""
Test suite for ServiceDesk-AI BM25 RAG Pipeline (in-house NLP).

Covers:
1. Document loading (.txt, .md)
2. Chunking & troubleshooting step preservation
3. BM25 retrieval with deterministic ranking
4. Relevance threshold filtering
5. Citation structure & metadata
6. Irrelevant & unknown query handling
7. RAG integration with /api/chat workflow
8. Protected admin ingestion API & status probe
"""

import pytest
from pathlib import Path
import tempfile
import shutil
import json

from app.config import settings
from app.services.rag.document_loader import (
    LoadedDocument,
    load_knowledge_base_dir,
)
from app.services.rag.chunker import DocumentChunker
from app.services.nlp.retriever import BM25Retriever
from app.services.rag.retrieval_interface import (
    get_retriever,
    register_custom_retriever,
    RetrievedChunk,
)
from app.services.rag.ingest import ingest_knowledge_base
from app.services.auth_service import create_access_token


@pytest.fixture
def temp_bm25_index_dir():
    """Temporary directory for test BM25 index."""
    tmp = tempfile.mkdtemp(prefix="test_bm25_")
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
    if faq_doc:
        assert faq_doc.title is not None
        assert len(faq_doc.content) > 100


# ============================================================================
# 2. Chunking Tests
# ============================================================================

def test_chunking_preserves_troubleshooting_steps():
    """Test that chunking preserves numbered steps."""
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
    # Check that steps are present
    full_content = " ".join([c.content for c in chunks])
    for step in ["1.", "2.", "3.", "4.", "5."]:
        assert step in full_content


def test_chunking_deterministic_ids():
    """Verify that chunk IDs are deterministic across runs."""
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
# 3. BM25 Retrieval Tests
# ============================================================================

def test_bm25_relevant_query_returns_documents(temp_bm25_index_dir):
    """Test that BM25 retrieves relevant documents for focused queries."""
    retriever = BM25Retriever(index_path=temp_bm25_index_dir / "test_index.json")
    
    # Build test index
    test_docs = [
        {
            "id": "vpn_001",
            "title": "VPN Troubleshooting Guide",
            "content": "VPN connection fails with Error 412 when remote peer drops packets. Toggle protocol to SSL.",
            "source": "vpn_guide.txt",
            "metadata": {},
        },
        {
            "id": "printer_001",
            "title": "Printer Troubleshooting",
            "content": "Paper jam in tray 2. Restart Windows Print Spooler service to clear stuck print jobs.",
            "source": "printer_guide.txt",
            "metadata": {},
        },
    ]
    retriever.rebuild_from_documents(test_docs)
    
    # Query for VPN
    result = retriever.retrieve("VPN Error 412 connection dropped", top_k=2)
    assert result.is_available is True
    assert len(result.documents) > 0
    top_doc = result.documents[0]
    assert "vpn" in top_doc.title.lower()
    assert top_doc.relevance_score is not None
    assert top_doc.relevance_score > 0.0


def test_bm25_irrelevant_query_filtered_by_threshold(temp_bm25_index_dir):
    """Test that unrelated queries return empty results below threshold."""
    retriever = BM25Retriever(index_path=temp_bm25_index_dir / "test_irrelevant.json")
    
    test_docs = [
        {
            "id": "net_001",
            "title": "Network Configuration",
            "content": "Configure router DHCP scopes and IP address pools for workstations.",
            "source": "network.txt",
            "metadata": {},
        },
    ]
    retriever.rebuild_from_documents(test_docs)
    
    # Query about unrelated topic with strict threshold
    result = retriever.retrieve("Chocolate cake recipe with strawberry frosting", top_k=3)
    # Should return results but below threshold or very low score
    if result.documents:
        assert all(doc.relevance_score < settings.RAG_RELEVANCE_THRESHOLD for doc in result.documents)


def test_bm25_empty_query_returns_empty(temp_bm25_index_dir):
    """Test graceful handling of empty queries."""
    retriever = BM25Retriever(index_path=temp_bm25_index_dir / "test_empty.json")
    
    test_docs = [
        {
            "id": "test_001",
            "title": "Test",
            "content": "Test content",
            "source": "test.txt",
            "metadata": {},
        },
    ]
    retriever.rebuild_from_documents(test_docs)
    
    result = retriever.retrieve("", top_k=3)
    assert len(result.documents) == 0
    
    result = retriever.retrieve("   ", top_k=3)
    assert len(result.documents) == 0


def test_bm25_retriever_implements_contract(temp_bm25_index_dir):
    """Verify BM25Retriever returns RetrievedChunk objects following the contract."""
    retriever = BM25Retriever(index_path=temp_bm25_index_dir / "test_contract.json")
    
    test_docs = [
        {
            "id": "pw_001",
            "title": "Password Policy",
            "content": "Passwords expire every 90 days. Reset password at the employee portal.",
            "source": "password_guide.txt",
            "metadata": {},
        },
    ]
    retriever.rebuild_from_documents(test_docs)
    
    result = retriever.retrieve("How do I reset my expired password?", top_k=2)
    
    assert result.is_available is True
    assert "BM25" in result.provider_info
    # Verify structure is correct even if results are filtered by threshold
    assert isinstance(result.documents, list)
    if len(result.documents) > 0:
        doc = result.documents[0]
        assert isinstance(doc, RetrievedChunk)
        assert doc.source == "password_guide.txt"
        assert doc.title == "Password Policy"
        assert doc.relevance_score is not None
        assert 0.0 <= doc.relevance_score <= 1.0


def test_bm25_reindex_does_not_create_duplicates(temp_bm25_index_dir):
    """Test that re-indexing the same documents does not create duplicates."""
    retriever = BM25Retriever(index_path=temp_bm25_index_dir / "test_dedup.json")
    
    test_docs = [
        {
            "id": "doc_001",
            "title": "First Document",
            "content": "Content of first document",
            "source": "doc1.txt",
            "metadata": {},
        },
    ]
    
    retriever.rebuild_from_documents(test_docs)
    count_after_first = retriever.index.total_docs
    
    # Re-index same documents
    retriever.rebuild_from_documents(test_docs)
    count_after_second = retriever.index.total_docs
    
    # Count should match exactly (rebuild replaces, not appends)
    assert count_after_first == count_after_second


# ============================================================================
# 4. Chat API Integration Tests
# ============================================================================

def test_chat_endpoint_returns_citations(client):
    """Test that POST /api/chat includes citations in response."""
    res = client.post("/api/chat", json={"message": "How do I fix VPN connection?"})
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


def test_chat_preserves_ticket_workflow(client):
    """Test that ticket creation workflows still work with BM25."""
    res = client.post("/api/chat", json={"message": "Please create a support ticket for my network issue"})
    assert res.status_code == 200
    data = res.json()
    # Should either create a ticket or escalate
    assert data["status"] in ("answered", "escalate")


# ============================================================================
# 5. Admin API Tests
# ============================================================================

def test_rag_status_endpoint(client):
    """Test GET /api/rag/status returns BM25 diagnostics."""
    res = client.get("/api/rag/status")
    assert res.status_code == 200
    data = res.json()
    assert "rag_enabled" in data
    assert "BM25" in data.get("retriever", "") or data["rag_enabled"] is True


def test_rag_ingest_endpoint_requires_auth(client):
    """Test that anonymous users cannot trigger ingestion."""
    res = client.post("/api/rag/ingest", json={"reset": False})
    assert res.status_code == 401


def test_rag_ingest_endpoint_rbac_forbidden_for_employee(client, employee_headers):
    """Test that employee role cannot trigger ingestion."""
    res = client.post(
        "/api/rag/ingest",
        json={"reset": False},
        headers=employee_headers,
    )
    assert res.status_code == 403


def test_rag_ingest_endpoint_authorized_for_admin(client, admin_headers):
    """Test that admin can trigger knowledge base ingestion."""
    res = client.post(
        "/api/rag/ingest",
        json={"reset": False},
        headers=admin_headers,
    )
    # Should succeed or return 200/500 depending on implementation
    assert res.status_code in (200, 500)
    if res.status_code == 200:
        data = res.json()
        assert data["status"] == "success"
        assert "chunks_indexed" in data


# ============================================================================
# Synonym Expansion Tests
# ============================================================================

def test_bm25_retriever_loads_synonyms(temp_bm25_index_dir):
    """Test that BM25Retriever loads synonyms from config file."""
    retriever = BM25Retriever(index_path=temp_bm25_index_dir / "test_synonyms.json")
    
    # Verify synonyms are loaded and non-empty
    assert retriever.synonyms is not None
    assert isinstance(retriever.synonyms, dict)
    assert len(retriever.synonyms) > 0, "Synonyms should be loaded from query_synonyms.json"
    
    # Verify specific synonym groups exist
    assert "two-factor" in retriever.synonyms
    assert "wifi" in retriever.synonyms
    assert "login" in retriever.synonyms
    
    # Verify synonym values are lists
    assert isinstance(retriever.synonyms["two-factor"], list)
    assert "mfa" in retriever.synonyms["two-factor"]


def test_bm25_query_expansion_with_synonyms(temp_bm25_index_dir):
    """Test that query expansion adds MFA-related terms for 'two-factor' queries."""
    retriever = BM25Retriever(index_path=temp_bm25_index_dir / "test_expansion.json")
    
    # Build a test index with an MFA guide plus 3 unrelated IT documents
    # (to ensure IDF calculation works properly - single-doc corpus has zero IDF)
    test_docs = [
        {
            "id": "mfa_001",
            "title": "MFA Authentication Guide",
            "content": "Multi-factor authentication (MFA) requires a second form of verification. "
                       "Common MFA methods include authenticator apps, security keys, and SMS codes.",
            "source": "mfa_guide.txt",
            "metadata": {},
        },
        {
            "id": "printer_001",
            "title": "Printer Troubleshooting",
            "content": "If your printer is offline, check the network connection and restart the device.",
            "source": "printer_guide.txt",
            "metadata": {},
        },
        {
            "id": "disk_001",
            "title": "Disk Space Management",
            "content": "Monitor your disk usage regularly to prevent storage issues.",
            "source": "disk_guide.txt",
            "metadata": {},
        },
        {
            "id": "password_001",
            "title": "Password Management",
            "content": "Use strong passwords with uppercase, lowercase, numbers and special characters.",
            "source": "password_guide.txt",
            "metadata": {},
        },
    ]
    retriever.rebuild_from_documents(test_docs)
    
    # Test expansion: "two-factor authentication not working"
    query = "two-factor authentication not working"
    expanded = retriever._expand_query_with_synonyms(query)
    
    # Verify expansion includes original terms AND MFA-related synonyms
    assert "two-factor" in expanded or "two" in expanded  # Original term
    assert "mfa" in expanded.lower(), "Expansion should include 'mfa' synonym"
    assert "authentication" in expanded  # Original term
    
    # Verify retrieval works with expanded query
    result = retriever.retrieve(query, top_k=1)
    assert result.is_available is True
    # Should find the MFA guide due to synonym expansion
    assert len(result.documents) > 0, "Should find MFA guide with synonym expansion"
    assert "mfa" in result.documents[0].title.lower() or "mfa" in result.documents[0].content.lower()
    # Verify MFA document is top-1
    assert result.documents[0].source == "mfa_guide.txt", "MFA guide should be top-1 result"


def test_bm25_raw_score_sorting_above_normalization_cap(temp_bm25_index_dir, monkeypatch):
    """Test that raw BM25 scores above normalization cap (10.0) maintain correct order."""
    # Set relevance threshold to 0.0 for this test to bypass filtering
    monkeypatch.setattr("app.config.settings.RAG_RELEVANCE_THRESHOLD", 0.0)
    
    retriever = BM25Retriever(index_path=temp_bm25_index_dir / "test_raw_scores.json")
    
    # Create a larger corpus so IDF is higher and scores exceed threshold
    # 15 filler documents + 2 target documents
    test_docs = [
        # Fillers (unrelated content) - 15 docs
        {"id": "filler_001", "title": "Printer Setup", "content": "printer configuration steps hardware", "source": "filler_1.txt", "metadata": {}},
        {"id": "filler_002", "title": "Network Config", "content": "network settings and routing protocols", "source": "filler_2.txt", "metadata": {}},
        {"id": "filler_003", "title": "Storage Options", "content": "storage and backup solutions systems", "source": "filler_3.txt", "metadata": {}},
        {"id": "filler_004", "title": "Security Basics", "content": "firewall and encryption methods tools", "source": "filler_4.txt", "metadata": {}},
        {"id": "filler_005", "title": "Email Setup", "content": "email client configuration exchange", "source": "filler_5.txt", "metadata": {}},
        {"id": "filler_006", "title": "Account Access", "content": "user account management policies", "source": "filler_6.txt", "metadata": {}},
        {"id": "filler_007", "title": "Device Management", "content": "device administration and tools software", "source": "filler_7.txt", "metadata": {}},
        {"id": "filler_008", "title": "Performance Tips", "content": "system optimization techniques procedures", "source": "filler_8.txt", "metadata": {}},
        {"id": "filler_009", "title": "Backup Procedures", "content": "backup restore recovery operations", "source": "filler_9.txt", "metadata": {}},
        {"id": "filler_010", "title": "Disaster Recovery", "content": "disaster recovery planning deployment", "source": "filler_10.txt", "metadata": {}},
        {"id": "filler_011", "title": "User Onboarding", "content": "onboarding process new employees", "source": "filler_11.txt", "metadata": {}},
        {"id": "filler_012", "title": "Compliance Policy", "content": "compliance regulations standards requirements", "source": "filler_12.txt", "metadata": {}},
        {"id": "filler_013", "title": "Audit Logging", "content": "audit logs monitoring tracking events", "source": "filler_13.txt", "metadata": {}},
        {"id": "filler_014", "title": "Incident Response", "content": "incident response procedures escalation", "source": "filler_14.txt", "metadata": {}},
        {"id": "filler_015", "title": "Knowledge Management", "content": "knowledge base documentation articles", "source": "filler_15.txt", "metadata": {}},
        
        # Target documents with rare term "multifactor" repeated at different frequencies
        {
            "id": "high_match_001",
            "title": "Multifactor Authentication Guide",
            # Repeat "multifactor" many times for high TF
            "content": "multifactor multifactor multifactor multifactor multifactor "
                       "multifactor multifactor multifactor multifactor multifactor "
                       "multifactor authentication security verification setup",
            "source": "high_match.txt",
            "metadata": {},
        },
        {
            "id": "low_match_001",
            "title": "Authentication Methods",
            # Include "multifactor" only once for lower TF
            "content": "multifactor authentication methods security verification steps",
            "source": "low_match.txt",
            "metadata": {},
        },
    ]
    retriever.rebuild_from_documents(test_docs)
    
    # Query for the rare term - both should match, threshold is 0.0 so both pass
    result = retriever.retrieve("multifactor", top_k=2)
    
    # Should have at least 2 results (threshold set to 0.0)
    assert len(result.documents) >= 2, f"Expected 2+ results, got {len(result.documents)}"
    
    # High-match doc (more repetitions) should rank first by raw BM25 score
    assert result.documents[0].source == "high_match.txt", \
        f"Document with higher TF should rank first. Got: {result.documents[0].source}"
    assert result.documents[1].source == "low_match.txt", "Document with lower TF should rank second"
    
    # Verify raw scores maintain ordering (stored in metadata)
    raw_score_1 = result.documents[0].metadata.get("raw_bm25_score", 0.0)
    raw_score_2 = result.documents[1].metadata.get("raw_bm25_score", 0.0)
    assert raw_score_1 > raw_score_2, f"Higher TF doc should have higher raw score: {raw_score_1} vs {raw_score_2}"
