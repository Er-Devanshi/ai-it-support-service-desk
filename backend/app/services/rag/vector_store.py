"""
ChromaDB Persistent Vector Store for ServiceDesk-AI.

Provides:
- Local disk persistence in `data/chroma_db`
- Repeatable upserting with deterministic chunk IDs
- Semantic similarity search using cosine distance
- Strict relevance threshold filtering
"""

from typing import List, Dict, Any, Optional
from pathlib import Path
import chromadb
from chromadb.config import Settings as ChromaSettings
from app.config import settings
from app.utils.logger import logger
from app.services.rag.retrieval_interface import RetrievedChunk
from app.services.rag.embeddings import BaseEmbeddingService, get_embedding_service


class ChromaVectorStore:
    """Manages persistent document embeddings and semantic vector retrieval in ChromaDB."""

    def __init__(
        self,
        persist_dir: Optional[Path] = None,
        collection_name: Optional[str] = None,
        embedding_service: Optional[BaseEmbeddingService] = None,
    ):
        self.persist_dir = Path(persist_dir or settings.CHROMA_PERSIST_DIR)
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        self.collection_name = collection_name or settings.CHROMA_COLLECTION_NAME
        self.embedding_service = embedding_service or get_embedding_service()

        # Initialize persistent client
        self.client = chromadb.PersistentClient(
            path=str(self.persist_dir),
            settings=ChromaSettings(anonymized_telemetry=False),
        )

        # Get or create collection with cosine space
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"},
        )
        logger.info(
            f"ChromaVectorStore initialized at '{self.persist_dir}' "
            f"collection='{self.collection_name}' (existing items={self.collection.count()})"
        )

    def add_chunks(self, chunks: List[RetrievedChunk]) -> int:
        """
        Add or update chunks in the vector collection.
        Uses upsert to ensure repeated runs do not duplicate documents.
        """
        if not chunks:
            return 0

        ids: List[str] = []
        documents: List[str] = []
        metadatas: List[Dict[str, Any]] = []

        for c in chunks:
            ids.append(c.chunk_id)
            documents.append(c.content)

            # Sanitize metadata values: Chroma requires bool, int, float, or str
            clean_meta = {
                "source": str(c.source),
                "title": str(c.title),
            }
            if c.metadata:
                for k, v in c.metadata.items():
                    if isinstance(v, (str, int, float, bool)):
                        clean_meta[k] = v
                    elif v is not None:
                        clean_meta[k] = str(v)

            metadatas.append(clean_meta)

        # Compute embeddings via active service
        embeddings = self.embedding_service.embed_documents(documents)

        # ChromaDB batch upsert
        batch_size = 64
        for i in range(0, len(ids), batch_size):
            end = i + batch_size
            self.collection.upsert(
                ids=ids[i:end],
                documents=documents[i:end],
                embeddings=embeddings[i:end],
                metadatas=metadatas[i:end],
            )

        logger.info(f"Upserted {len(chunks)} chunk(s) into ChromaDB collection '{self.collection_name}'")
        return len(chunks)

    def search(
        self,
        query: str,
        top_k: Optional[int] = None,
        relevance_threshold: Optional[float] = None,
    ) -> List[RetrievedChunk]:
        """
        Semantic vector search for relevant document chunks.
        Applies relevance threshold and formats similarity scores.
        """
        if not query or not query.strip():
            return []

        top_k = top_k or settings.RAG_TOP_K
        threshold = relevance_threshold if relevance_threshold is not None else settings.RAG_RELEVANCE_THRESHOLD

        total_in_db = self.collection.count()
        if total_in_db == 0:
            return []

        n_results = min(top_k, total_in_db)
        query_emb = self.embedding_service.embed_query(query.strip())

        try:
            results = self.collection.query(
                query_embeddings=[query_emb],
                n_results=n_results,
                include=["documents", "metadatas", "distances"],
            )
        except Exception as e:
            logger.error(f"ChromaDB search query failed: {e}")
            return []

        retrieved: List[RetrievedChunk] = []

        if not results or not results["ids"] or not results["ids"][0]:
            return []

        doc_ids = results["ids"][0]
        docs = results["documents"][0] if results["documents"] else []
        metas = results["metadatas"][0] if results["metadatas"] else []
        distances = results["distances"][0] if results["distances"] else []

        for idx, chunk_id in enumerate(doc_ids):
            content = docs[idx] if idx < len(docs) else ""
            meta = metas[idx] if idx < len(metas) else {}
            dist = distances[idx] if idx < len(distances) else 1.0

            # For cosine distance d in [0, 2], similarity is 1 - d
            # When distance is close to 0, similarity is close to 1.0
            similarity = round(max(0.0, min(1.0, 1.0 - dist)), 3)

            # Apply relevance threshold filter
            if similarity < threshold:
                logger.debug(f"Chunk '{chunk_id}' scored {similarity} < threshold {threshold}, filtering out")
                continue

            retrieved.append(
                RetrievedChunk(
                    chunk_id=chunk_id,
                    source=meta.get("source", "knowledge_base"),
                    title=meta.get("title", "IT Knowledge Document"),
                    content=content,
                    relevance_score=similarity,
                    metadata=meta,
                )
            )

        return retrieved

    def count(self) -> int:
        """Return total number of chunks stored in vector database."""
        return self.collection.count()

    def reset(self) -> None:
        """Clear all records in the collection for full re-indexing."""
        self.client.delete_collection(self.collection_name)
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"},
        )
        logger.info(f"ChromaDB collection '{self.collection_name}' reset.")

    def get_status(self) -> Dict[str, Any]:
        """Return diagnostic status of the vector store."""
        return {
            "persist_dir": str(self.persist_dir),
            "collection_name": self.collection_name,
            "document_count": self.count(),
            "embedding_model": self.embedding_service.model_name,
            "dimension": self.embedding_service.dimension,
            "status": "active",
        }


# Global vector store instance
_active_vector_store: Optional[ChromaVectorStore] = None


def get_vector_store(force_new: bool = False, embedding_service: Optional[BaseEmbeddingService] = None) -> ChromaVectorStore:
    """Return or initialize the singleton ChromaVectorStore."""
    global _active_vector_store
    if force_new or _active_vector_store is None:
        _active_vector_store = ChromaVectorStore(embedding_service=embedding_service)
    return _active_vector_store


def set_vector_store(store: Optional[ChromaVectorStore]):
    """Override active vector store (useful for tests)."""
    global _active_vector_store
    _active_vector_store = store
