"""
BM25 retriever for knowledge base search.

BM25 (Best Matching 25) is a probabilistic ranking function.
Parameters: k1=1.5 (term frequency saturation), b=0.75 (length normalization).

Implemented from scratch with numpy. No external ranking library.
"""

import json
import math
from typing import List, Dict, Tuple, Optional
from pathlib import Path
from collections import defaultdict, Counter

import numpy as np

from app.services.nlp.tokenizer import tokenize
from app.utils.logger import logger


class BM25Index:
    """
    BM25 retrieval index built from document chunks.
    
    Stores:
    - Document collection
    - Inverted index (term -> doc_ids and frequencies)
    - Document statistics (length, avg length)
    """

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        """
        Initialize BM25 index.
        
        Args:
            k1: Term frequency saturation parameter (default 1.5)
            b: Length normalization parameter (default 0.75)
        """
        self.k1 = k1
        self.b = b
        
        # Documents: list of {id, title, content, source, ...}
        self.documents = {}  # doc_id -> doc_dict
        self.doc_ids = []  # ordered list of doc IDs
        
        # Inverted index: term -> {doc_id -> frequency}
        self.inverted_index = defaultdict(dict)
        
        # Document statistics
        self.doc_lengths = {}  # doc_id -> token count
        self.avg_doc_length = 0.0
        
        # Metadata
        self.vocab_size = 0
        self.total_docs = 0

    def add_document(self, doc_id: str, title: str, content: str, source: str, metadata: Optional[Dict] = None) -> None:
        """
        Add a document to the index.
        """
        # Tokenize content (include title in indexing for importance)
        full_text = f"{title} {content}"
        tokens = tokenize(full_text, remove_stopwords=True, stem=True)
        
        # Store document
        self.documents[doc_id] = {
            "id": doc_id,
            "title": title,
            "content": content,
            "source": source,
            "metadata": metadata or {},
        }
        self.doc_ids.append(doc_id)
        self.doc_lengths[doc_id] = len(tokens)
        self.total_docs += 1
        
        # Update inverted index
        term_freqs = Counter(tokens)
        for term, freq in term_freqs.items():
            self.inverted_index[term][doc_id] = freq

    def finalize(self) -> None:
        """
        Finalize the index after all documents are added.
        Computes document statistics.
        """
        if self.total_docs == 0:
            self.avg_doc_length = 0.0
            return
        
        self.avg_doc_length = np.mean(list(self.doc_lengths.values()))
        self.vocab_size = len(self.inverted_index)
        
        logger.info(
            f"BM25 index finalized: {self.total_docs} docs, "
            f"{self.vocab_size} vocab, avg_doc_len={self.avg_doc_length:.1f}"
        )

    def search(self, query: str, top_k: int = 3) -> List[Tuple[str, float]]:
        """
        Search for the top-k most relevant documents.
        
        Returns:
            List of (doc_id, bm25_score) tuples sorted by score descending
        """
        # Tokenize query
        query_tokens = tokenize(query, remove_stopwords=True, stem=True)
        query_freqs = Counter(query_tokens)
        
        # Compute BM25 scores for each document
        scores = {}
        
        for doc_id in self.doc_ids:
            score = 0.0
            doc_len = self.doc_lengths[doc_id]
            
            for term, query_freq in query_freqs.items():
                # IDF: inverse document frequency
                doc_freq = len(self.inverted_index.get(term, {}))
                if doc_freq == 0:
                    continue  # Term not in any document
                
                idf = math.log((self.total_docs - doc_freq + 0.5) / (doc_freq + 0.5) + 1.0)
                
                # Term frequency in document
                tf = self.inverted_index[term].get(doc_id, 0.0)
                
                # BM25 formula
                numerator = tf * (self.k1 + 1)
                denominator = tf + self.k1 * (
                    1 - self.b + self.b * (doc_len / self.avg_doc_length)
                )
                score += idf * (numerator / denominator)
            
            if score > 0:
                scores[doc_id] = score
        
        # Sort by score descending
        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return ranked[:top_k]

    def save(self, index_path: Path) -> None:
        """
        Save index to JSON file.
        """
        index_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Convert inverted index to JSON-serializable format
        inverted_index_json = {
            term: list(doc_freq_dict.items())
            for term, doc_freq_dict in self.inverted_index.items()
        }
        
        index_data = {
            "k1": self.k1,
            "b": self.b,
            "documents": self.documents,
            "doc_ids": self.doc_ids,
            "doc_lengths": self.doc_lengths,
            "avg_doc_length": self.avg_doc_length,
            "vocab_size": self.vocab_size,
            "total_docs": self.total_docs,
            "inverted_index": inverted_index_json,
        }
        
        with open(index_path, "w") as f:
            json.dump(index_data, f, indent=2)
        
        logger.info(f"BM25 index saved to {index_path}")

    @classmethod
    def load(cls, index_path: Path) -> "BM25Index":
        """
        Load index from JSON file.
        """
        with open(index_path, "r") as f:
            index_data = json.load(f)
        
        index = cls(k1=index_data["k1"], b=index_data["b"])
        
        index.documents = index_data["documents"]
        index.doc_ids = index_data["doc_ids"]
        index.doc_lengths = index_data["doc_lengths"]
        index.avg_doc_length = index_data["avg_doc_length"]
        index.vocab_size = index_data["vocab_size"]
        index.total_docs = index_data["total_docs"]
        
        # Restore inverted index
        inverted_index_json = index_data["inverted_index"]
        index.inverted_index = defaultdict(dict)
        for term, doc_freq_list in inverted_index_json.items():
            index.inverted_index[term] = dict(doc_freq_list)
        
        logger.info(f"BM25 index loaded from {index_path}")
        return index
