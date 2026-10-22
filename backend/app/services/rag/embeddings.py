"""
Embedding service abstraction for ServiceDesk-AI RAG pipeline.

Supports:
1. Local SentenceTransformers (all-MiniLM-L6-v2):
   - Fast, 384-dimensional dense embeddings
   - Runs locally without external paid APIs
2. Mock Embedding Service:
   - Deterministic semantic pseudo-embeddings for offline testing and air-gapped CI
   - Preserves high similarity for shared semantic keywords without model downloads
"""

from abc import ABC, abstractmethod
from typing import List, Optional
import math
import hashlib
import re
from app.config import settings
from app.utils.logger import logger


class BaseEmbeddingService(ABC):
    """Abstract embedding contract."""

    @property
    @abstractmethod
    def dimension(self) -> int:
        """Embedding vector dimension."""
        pass

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Name of the active model."""
        pass

    @abstractmethod
    def embed_query(self, query: str) -> List[float]:
        """Compute embedding vector for a single query."""
        pass

    @abstractmethod
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Compute embedding vectors for a batch of text passages."""
        pass


class LocalSentenceTransformerEmbedding(BaseEmbeddingService):
    """Local SentenceTransformer embedding using all-MiniLM-L6-v2."""

    def __init__(self, model_name: Optional[str] = None):
        self._model_name = model_name or settings.EMBEDDING_MODEL
        self._model = None
        self._dimension = 384

    def _ensure_model_loaded(self):
        """Lazy load the sentence-transformers model on first invocation."""
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                logger.info(f"Loading local SentenceTransformer model: {self._model_name}")
                self._model = SentenceTransformer(self._model_name)
                # Test dimension
                test_emb = self._model.encode("test", convert_to_numpy=True)
                self._dimension = len(test_emb)
                logger.info(f"Loaded {self._model_name} successfully (dimension={self._dimension})")
            except Exception as e:
                logger.error(f"Failed to load embedding model '{self._model_name}': {e}")
                raise RuntimeError(
                    f"Embedding model '{self._model_name}' could not be initialized: {e}. "
                    "Ensure internet connection is available for the initial download, "
                    "or configure a pre-cached model path."
                ) from e

    @property
    def dimension(self) -> int:
        return self._dimension

    @property
    def model_name(self) -> str:
        return self._model_name

    def embed_query(self, query: str) -> List[float]:
        self._ensure_model_loaded()
        embedding = self._model.encode(query, convert_to_numpy=True, normalize_embeddings=True)
        return embedding.tolist()

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        self._ensure_model_loaded()
        embeddings = self._model.encode(texts, convert_to_numpy=True, normalize_embeddings=True, batch_size=32)
        return embeddings.tolist()


class MockEmbeddingService(BaseEmbeddingService):
    """
    Deterministic semantic hash embedding for testing and offline development.
    Maps key IT vocabulary to specific coordinate bands so semantic similarity
    is realistic without requiring PyTorch or HuggingFace model downloads.
    """

    def __init__(self, dimension: int = 384, model_name: str = "mock-semantic-embedder"):
        self._dimension = dimension
        self._model_name = model_name

        # Semantic cluster anchor keywords
        self._semantic_domains = [
            ("network", ["wifi", "wi-fi", "internet", "router", "dhcp", "ip", "ethernet", "connection", "offline"]),
            ("vpn", ["vpn", "tunnel", "anyconnect", "gateway", "remote", "pulse", "cisco", "split"]),
            ("account", ["password", "reset", "locked", "account", "unlock", "login", "credentials", "user"]),
            ("security", ["mfa", "2fa", "authenticator", "phishing", "suspicious", "token", "code", "incident"]),
            ("hardware", ["printer", "print", "spooler", "paper", "jam", "laptop", "monitor", "dock", "usb"]),
            ("software", ["software", "install", "update", "application", "license", "browser", "chrome"]),
            ("performance", ["slow", "cpu", "memory", "ram", "freeze", "crash", "task", "reboot"]),
            ("email", ["email", "outlook", "sync", "inbox", "mail", "exchange", "calendar"]),
        ]

    @property
    def dimension(self) -> int:
        return self._dimension

    @property
    def model_name(self) -> str:
        return self._model_name

    def _generate_vector(self, text: str) -> List[float]:
        """Generate normalized 384-d vector with semantic domain activation."""
        tokens = set(re.findall(r"\w+", text.lower()))
        vector = [0.0] * self._dimension

        # 1. Base deterministic noise based on text hash
        text_hash = hashlib.md5(text.encode("utf-8")).digest()
        for i in range(self._dimension):
            byte_val = text_hash[i % len(text_hash)]
            vector[i] = ((byte_val / 255.0) - 0.5) * 0.1

        # 2. Domain activation bands
        band_size = self._dimension // len(self._semantic_domains)
        for domain_idx, (domain_name, keywords) in enumerate(self._semantic_domains):
            overlap = tokens.intersection(keywords)
            if overlap:
                intensity = len(overlap) * 0.8
                start_pos = domain_idx * band_size
                for i in range(start_pos, min(start_pos + band_size, self._dimension)):
                    vector[i] += intensity

        # 3. Normalize vector to unit length (L2 norm = 1.0)
        norm = math.sqrt(sum(x * x for x in vector))
        if norm > 0:
            vector = [x / norm for x in vector]

        return vector

    def embed_query(self, query: str) -> List[float]:
        return self._generate_vector(query)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return [self._generate_vector(t) for t in texts]


# Global embedding singleton
_active_embedding_service: Optional[BaseEmbeddingService] = None


def get_embedding_service(force_mock: bool = False) -> BaseEmbeddingService:
    """Return the configured embedding service instance."""
    global _active_embedding_service
    if force_mock:
        return MockEmbeddingService()

    if _active_embedding_service is not None:
        return _active_embedding_service

    # Default to LocalSentenceTransformerEmbedding
    try:
        _active_embedding_service = LocalSentenceTransformerEmbedding()
    except Exception as e:
        logger.warning(f"Could not initialize local sentence-transformers, falling back to mock: {e}")
        _active_embedding_service = MockEmbeddingService()

    return _active_embedding_service


def set_embedding_service(service: Optional[BaseEmbeddingService]):
    """Override active embedding service (useful for testing)."""
    global _active_embedding_service
    _active_embedding_service = service
