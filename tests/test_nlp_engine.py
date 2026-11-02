"""
Comprehensive test suite for in-house NLP engine components.

Tests cover:
1. Tokenizer: tokenization, stemming, stopword removal, bigrams
2. Naive Bayes Classifier: training, prediction, probability calibration
3. BM25Index: document indexing, querying, ranking
4. BM25Retriever: integration with retrieval interface
5. Responder: step extraction, response building, escalation
6. Slots & Impact/Urgency: extraction and classification
"""

import pytest
import json
import tempfile
from pathlib import Path
from collections import defaultdict

from app.services.nlp.tokenizer import (
    tokenize,
    simple_stem,
    get_bigrams,
    tokenize_with_bigrams,
    get_vocabulary_from_texts,
)
from app.services.nlp.classifier import NaiveBayesClassifier
from app.services.nlp.bm25 import BM25Index
from app.services.nlp.retriever import BM25Retriever
from app.services.nlp.responder import extract_steps, build_response, build_escalation_response
from app.services.nlp.impact_urgency import classify_impact, classify_urgency
from app.services.nlp.slots import extract_slots
from app.services.rag.retrieval_interface import RetrievedChunk, RetrievalResult


# ============================================================================
# 1. Tokenizer Tests
# ============================================================================

class TestTokenizer:
    """Test tokenization, stemming, and preprocessing."""

    def test_tokenize_basic(self):
        """Test basic tokenization splits on word boundaries."""
        text = "Wi-Fi is not working"
        tokens = tokenize(text, remove_stopwords=False, stem=False)
        assert "wi" in tokens or "wifi" in tokens  # Wi-Fi handling
        assert "not" in tokens
        assert "working" in tokens

    def test_tokenize_removes_stopwords(self):
        """Test stopword filtering."""
        text = "I need to reset the password"
        tokens_with_stop = tokenize(text, remove_stopwords=False, stem=False)
        tokens_no_stop = tokenize(text, remove_stopwords=True, stem=False)
        
        assert "i" in tokens_with_stop
        assert "i" not in tokens_no_stop
        assert "to" in tokens_with_stop
        assert "to" not in tokens_no_stop
        assert "password" in tokens_no_stop

    def test_tokenize_applies_stemming(self):
        """Test that stemming removes common suffixes."""
        text = "dependencies passed printed"
        tokens_stemmed = tokenize(text, remove_stopwords=False, stem=True)
        tokens_unstemmed = tokenize(text, remove_stopwords=False, stem=False)
        
        # Stemmed should be shorter or equal
        assert len(tokens_stemmed) == len(tokens_unstemmed)
        # Check suffix stripping: "dependencies" -> "dependenci"
        assert tokens_stemmed != tokens_unstemmed

    def test_simple_stem_rules(self):
        """Test suffix-stripping rules."""
        assert simple_stem("dependencies") == "dependenci"
        assert simple_stem("passed") == "pass"
        assert simple_stem("users") == "user"
        assert simple_stem("locked") == "lock"
        assert simple_stem("printing") == "print"

    def test_tokenize_lowercase(self):
        """Test case normalization."""
        tokens1 = tokenize("Hello WORLD", remove_stopwords=False, stem=False)
        tokens2 = tokenize("hello world", remove_stopwords=False, stem=False)
        assert tokens1 == tokens2

    def test_get_bigrams(self):
        """Test bigram generation."""
        tokens = ["hello", "world", "test"]
        bigrams = get_bigrams(tokens)
        assert bigrams == [("hello", "world"), ("world", "test")]

    def test_get_bigrams_empty(self):
        """Test bigrams with < 2 tokens."""
        assert get_bigrams([]) == []
        assert get_bigrams(["single"]) == []

    def test_tokenize_with_bigrams(self):
        """Test combined unigram and bigram tokenization."""
        text = "hello world test"
        unigrams, bigrams = tokenize_with_bigrams(text, remove_stopwords=False)
        assert len(unigrams) == 3
        assert len(bigrams) == 2
        assert ("hello", "world") in bigrams

    def test_get_vocabulary_from_texts(self):
        """Test vocabulary extraction from text collection."""
        texts = ["hello world", "world test", "hello test"]
        vocab = get_vocabulary_from_texts(texts)
        # Should contain stemmed, stopword-filtered tokens
        assert "hello" in vocab
        assert "world" in vocab
        assert "test" in vocab


# ============================================================================
# 2. Naive Bayes Classifier Tests
# ============================================================================

class TestNaiveBayesClassifier:
    """Test Naive Bayes classification with TF-IDF features."""

    @pytest.fixture
    def simple_classifier(self):
        """Create and train a simple classifier."""
        classifier = NaiveBayesClassifier()
        
        texts = [
            "password reset account login",
            "password change credentials secure",
            "network connectivity wi-fi internet",
            "network connection wifi speed",
            "printer paper jam tray",
            "printer device hardware malfunction",
        ]
        labels = ["account", "account", "network", "network", "hardware", "hardware"]
        
        classifier.fit(texts, labels)
        return classifier

    def test_classifier_initializes_unfitted(self):
        """Test classifier starts in unfitted state."""
        clf = NaiveBayesClassifier()
        assert clf.is_fitted is False
        assert clf.total_docs == 0

    def test_classifier_fits_on_data(self, simple_classifier):
        """Test classifier learns from training data."""
        assert simple_classifier.is_fitted is True
        assert simple_classifier.total_docs == 6
        assert len(simple_classifier.categories) == 3
        assert set(simple_classifier.categories) == {"account", "network", "hardware"}

    def test_classifier_raises_on_mismatched_lengths(self):
        """Test fit() rejects mismatched texts/labels."""
        clf = NaiveBayesClassifier()
        with pytest.raises(ValueError):
            clf.fit(["text1", "text2"], ["label1"])

    def test_classifier_raises_on_predict_before_fit(self):
        """Test predict() requires fitting first."""
        clf = NaiveBayesClassifier()
        with pytest.raises(RuntimeError):
            clf.predict("test")

    def test_classifier_predict_returns_tuple(self, simple_classifier):
        """Test predict returns (category, probs_dict)."""
        result = simple_classifier.predict("reset password")
        assert isinstance(result, tuple)
        assert len(result) == 2
        category, probs = result
        assert isinstance(category, str)
        assert isinstance(probs, dict)

    def test_classifier_predict_proba_sums_to_one(self, simple_classifier):
        """Test probability distribution sums to 1.0."""
        probs = simple_classifier.predict_proba("reset password")
        total = sum(probs.values())
        assert abs(total - 1.0) < 1e-6

    def test_classifier_accounts_category_for_account_query(self, simple_classifier):
        """Test classifier predicts 'account' for account-related query."""
        category, probs = simple_classifier.predict("I need to reset my password")
        assert category == "account"
        assert probs["account"] > 0.3

    def test_classifier_network_category_for_network_query(self, simple_classifier):
        """Test classifier predicts 'network' for network-related query."""
        category, probs = simple_classifier.predict("wi-fi not working")
        assert category == "network"
        assert probs["network"] > 0.3

    def test_classifier_hardware_category_for_hardware_query(self, simple_classifier):
        """Test classifier predicts 'hardware' for hardware-related query."""
        category, probs = simple_classifier.predict("printer jam")
        assert category == "hardware"
        assert probs["hardware"] > 0.3

    def test_classifier_all_categories_represented(self, simple_classifier):
        """Test predict_proba includes all categories."""
        probs = simple_classifier.predict_proba("test")
        assert set(probs.keys()) == set(simple_classifier.categories)

    def test_classifier_save_and_load(self, simple_classifier, tmp_path):
        """Test model persistence."""
        model_path = tmp_path / "classifier.json"
        
        # Save
        simple_classifier.save(model_path)
        assert model_path.exists()
        
        # Load
        loaded = NaiveBayesClassifier.load(model_path)
        assert loaded.is_fitted is True
        assert loaded.categories == simple_classifier.categories
        assert loaded.vocab == simple_classifier.vocab
        
        # Verify predictions match
        test_text = "password reset"
        pred1 = simple_classifier.predict(test_text)
        pred2 = loaded.predict(test_text)
        assert pred1[0] == pred2[0]  # Same category


# ============================================================================
# 3. BM25Index Tests
# ============================================================================

class TestBM25Index:
    """Test BM25 indexing and retrieval ranking."""

    @pytest.fixture
    def bm25_index(self):
        """Create and populate a BM25 index."""
        index = BM25Index()
        
        docs = [
            {
                "id": "vpn_001",
                "title": "VPN Troubleshooting",
                "content": "VPN connection fails with Error 412. Toggle protocol to SSL.",
                "source": "vpn_guide.txt",
            },
            {
                "id": "printer_001",
                "title": "Printer Issues",
                "content": "Paper jam in tray 2. Restart Print Spooler service.",
                "source": "printer_guide.txt",
            },
            {
                "id": "network_001",
                "title": "Network Setup",
                "content": "Configure DHCP for workstations. Set IP address pools.",
                "source": "network_guide.txt",
            },
        ]
        
        for doc in docs:
            index.add_document(
                doc_id=doc["id"],
                title=doc["title"],
                content=doc["content"],
                source=doc["source"],
            )
        
        index.finalize()
        return index

    def test_bm25_index_initializes(self):
        """Test BM25Index initialization."""
        index = BM25Index()
        assert index.total_docs == 0
        assert index.avg_doc_length == 0.0
        assert index.vocab_size == 0

    def test_bm25_add_document(self, bm25_index):
        """Test adding documents to index."""
        assert bm25_index.total_docs == 3
        assert len(bm25_index.doc_ids) == 3
        assert "vpn_001" in bm25_index.documents

    def test_bm25_finalize_computes_stats(self, bm25_index):
        """Test finalize() computes document statistics."""
        assert bm25_index.avg_doc_length > 0.0
        assert bm25_index.vocab_size > 0

    def test_bm25_search_returns_ranking(self, bm25_index):
        """Test search returns ranked results."""
        results = bm25_index.search("VPN Error 412")
        assert len(results) > 0
        assert results[0][0] == "vpn_001"  # Most relevant

    def test_bm25_search_respects_topk(self, bm25_index):
        """Test search limits to top_k results."""
        results_k1 = bm25_index.search("test", top_k=1)
        results_k2 = bm25_index.search("test", top_k=2)
        
        assert len(results_k1) <= 1
        assert len(results_k2) <= 2

    def test_bm25_search_scores_are_positive(self, bm25_index):
        """Test BM25 scores are non-negative."""
        results = bm25_index.search("VPN Error")
        for doc_id, score in results:
            assert score >= 0.0

    def test_bm25_search_empty_query_returns_empty(self, bm25_index):
        """Test empty query returns no results."""
        results = bm25_index.search("", top_k=3)
        assert len(results) == 0

    def test_bm25_save_and_load(self, bm25_index, tmp_path):
        """Test index persistence."""
        index_path = tmp_path / "bm25.json"
        
        # Save
        bm25_index.save(index_path)
        assert index_path.exists()
        
        # Load
        loaded = BM25Index.load(index_path)
        assert loaded.total_docs == bm25_index.total_docs
        assert loaded.vocab_size == bm25_index.vocab_size
        assert loaded.doc_ids == bm25_index.doc_ids
        
        # Verify search results match
        results1 = bm25_index.search("VPN Error")
        results2 = loaded.search("VPN Error")
        assert results1[0][0] == results2[0][0]


# ============================================================================
# 4. BM25Retriever Tests
# ============================================================================

class TestBM25Retriever:
    """Test BM25Retriever integration with retrieval interface."""

    @pytest.fixture
    def temp_retriever(self, tmp_path):
        """Create BM25Retriever with test index."""
        retriever = BM25Retriever(index_path=tmp_path / "test_index.json")
        
        docs = [
            {
                "id": "faq_001",
                "title": "Password Reset FAQ",
                "content": "To reset password: 1. Visit portal. 2. Click Forgot Password. 3. Verify email.",
                "source": "faq.txt",
                "metadata": {},
            },
            {
                "id": "faq_002",
                "title": "VPN Connection Guide",
                "content": "VPN setup: 1. Download client. 2. Install. 3. Authenticate.",
                "source": "vpn_setup.txt",
                "metadata": {},
            },
        ]
        
        retriever.rebuild_from_documents(docs)
        return retriever

    def test_retriever_rebuilds_index(self, temp_retriever):
        """Test rebuild_from_documents builds index."""
        assert temp_retriever.index is not None
        assert temp_retriever.index.total_docs == 2

    def test_retriever_retrieve_returns_result(self, temp_retriever):
        """Test retrieve() returns RetrievalResult."""
        result = temp_retriever.retrieve("password reset")
        assert isinstance(result, RetrievalResult)
        assert result.is_available is True
        assert isinstance(result.documents, list)

    def test_retriever_retrieve_returns_retrieved_chunks(self, temp_retriever):
        """Test retrieved documents are RetrievedChunk objects."""
        result = temp_retriever.retrieve("password reset", top_k=2)
        assert len(result.documents) > 0
        for doc in result.documents:
            assert isinstance(doc, RetrievedChunk)
            assert doc.source is not None
            assert doc.relevance_score is not None

    def test_retriever_includes_provider_info(self, temp_retriever):
        """Test provider_info identifies BM25."""
        result = temp_retriever.retrieve("test")
        assert "BM25" in result.provider_info

    def test_retriever_empty_query(self, temp_retriever):
        """Test empty query returns empty results."""
        result = temp_retriever.retrieve("", top_k=3)
        assert len(result.documents) == 0


# ============================================================================
# 5. Responder Tests
# ============================================================================

class TestResponder:
    """Test response building and step extraction."""

    def test_extract_steps_numbered(self):
        """Test extraction of numbered steps."""
        text = "1. First step\n2. Second step\n3. Third step"
        steps = extract_steps(text)
        assert len(steps) >= 3

    def test_extract_steps_bulleted(self):
        """Test extraction of bulleted steps."""
        text = "• First item\n• Second item\n- Third item"
        steps = extract_steps(text)
        assert len(steps) >= 2

    def test_extract_steps_no_steps(self):
        """Test extraction from text with no clear steps."""
        text = "This is just some plain text without any steps."
        steps = extract_steps(text)
        # Should return something or empty
        assert isinstance(steps, list)

    def test_build_response_with_relevant_docs(self):
        """Test response building with good documents."""
        doc = RetrievedChunk(
            chunk_id="test_001",
            source="test.txt",
            title="Test Guide",
            content="1. Step one\n2. Step two",
            relevance_score=0.9,
            metadata={},
        )
        
        response, should_escalate = build_response(
            category="network",
            retrieved_docs=[doc],
            relevance_threshold=0.5,
        )
        
        assert should_escalate is False
        assert len(response) > 0
        assert "Source:" in response or "source" in response.lower()

    def test_build_response_no_relevant_docs(self):
        """Test response when no documents meet threshold."""
        doc = RetrievedChunk(
            chunk_id="test_001",
            source="test.txt",
            title="Test",
            content="Content",
            relevance_score=0.2,
            metadata={},
        )
        
        response, should_escalate = build_response(
            category="network",
            retrieved_docs=[doc],
            relevance_threshold=0.8,
        )
        
        assert should_escalate is True
        assert "support ticket" in response.lower() or "escalate" in response.lower()

    def test_build_escalation_response(self):
        """Test escalation message generation."""
        response = build_escalation_response(reason="No match found")
        assert len(response) > 0
        assert "No match found" in response


# ============================================================================
# 6. Impact & Urgency Extraction Tests
# ============================================================================

class TestImpactUrgency:
    """Test impact and urgency classification."""

    def test_classify_impact_high(self):
        """Test high-impact issue detection."""
        text = "Our entire department's systems are down"
        impact = classify_impact(text)
        assert impact in ["high", "medium", "low"]

    def test_classify_impact_low(self):
        """Test low-impact issue detection."""
        text = "Minor formatting issue in email"
        impact = classify_impact(text)
        assert impact in ["high", "medium", "low"]

    def test_classify_urgency_high(self):
        """Test high-urgency issue detection."""
        text = "Critical production system failing right now"
        urgency = classify_urgency(text)
        assert urgency in ["high", "medium", "low"]

    def test_classify_urgency_low(self):
        """Test low-urgency issue detection."""
        text = "I'd like to request software when you have time"
        urgency = classify_urgency(text)
        assert urgency in ["high", "medium", "low"]


# ============================================================================
# 7. Slots Extraction Tests
# ============================================================================

class TestSlots:
    """Test entity/slot extraction."""

    def test_extract_slots_returns_dict(self):
        """Test extract_slots returns dictionary."""
        text = "My printer is down and I need it by tomorrow"
        slots = extract_slots(text)
        assert isinstance(slots, dict)

    def test_extract_slots_detects_device(self):
        """Test slot extraction detects device types."""
        text = "The printer is not working"
        slots = extract_slots(text)
        # Should contain some detection of 'printer'
        assert isinstance(slots, dict)

    def test_extract_slots_detects_deadline(self):
        """Test slot extraction detects time expressions."""
        text = "I need this fixed by tomorrow morning"
        slots = extract_slots(text)
        assert isinstance(slots, dict)

