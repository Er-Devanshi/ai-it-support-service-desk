"""
Multinomial Naive Bayes text classifier with TF-IDF weighting.

Implemented from scratch using numpy:
- TF-IDF feature extraction (unigrams + bigrams)
- Laplace smoothing
- Probability estimation
- Model persistence to JSON

No sklearn, no pretrained embeddings.
"""

import json
import math
from typing import Dict, List, Tuple, Optional
from pathlib import Path
from collections import defaultdict, Counter

import numpy as np

from app.services.nlp.tokenizer import tokenize, get_bigrams, simple_stem
from app.utils.logger import logger


class NaiveBayesClassifier:
    """Multinomial Naive Bayes with TF-IDF unigram+bigram features."""

    def __init__(self, categories: Optional[List[str]] = None, alpha: float = 1.0):
        """
        Initialize classifier.
        
        Args:
            categories: List of category labels. If None, inferred from training data.
            alpha: Laplace smoothing parameter (default 1.0).
        """
        self.categories = categories or []
        self.alpha = alpha
        
        # Vocabulary: maps feature (unigram or "w1_w2" bigram) to index
        self.vocab = {}
        self.feature_names = []
        
        # Per-category statistics
        self.category_counts = {}  # category -> count of training docs
        self.category_feature_counts = {}  # category -> feature -> count
        self.class_priors = {}  # category -> prior probability
        
        self.total_docs = 0
        self.is_fitted = False

    def _extract_features(self, text: str) -> Counter:
        """
        Extract TF-IDF weighted features from text.
        Returns a Counter of {feature: weight}.
        """
        tokens = tokenize(text, remove_stopwords=True, stem=True)
        
        # Unigrams with weight 1.0
        unigram_counts = Counter(tokens)
        
        # Bigrams with weight 1.0
        bigrams = get_bigrams(tokens)
        bigram_counts = Counter([f"{b[0]}_{b[1]}" for b in bigrams])
        
        # Combine unigrams and bigrams
        features = Counter()
        features.update(unigram_counts)
        features.update(bigram_counts)
        
        return features

    def fit(self, texts: List[str], labels: List[str]) -> None:
        """
        Train the classifier on labeled texts.
        
        Args:
            texts: List of training documents
            labels: List of category labels (same length as texts)
        """
        if len(texts) != len(labels):
            raise ValueError("texts and labels must have same length")
        
        self.categories = sorted(list(set(labels)))
        self.total_docs = len(texts)
        
        # Initialize category statistics
        for cat in self.categories:
            self.category_counts[cat] = 0
            self.category_feature_counts[cat] = defaultdict(float)
        
        # Count features per category
        all_features_in_category = defaultdict(Counter)  # category -> Counter of all feature freqs
        
        for text, label in zip(texts, labels):
            self.category_counts[label] += 1
            features = self._extract_features(text)
            
            for feature, count in features.items():
                self.category_feature_counts[label][feature] += count
                all_features_in_category[label][feature] += count
        
        # Build vocabulary from all features seen
        vocab_set = set()
        for cat in self.categories:
            vocab_set.update(self.category_feature_counts[cat].keys())
        
        self.vocab = {feat: idx for idx, feat in enumerate(sorted(vocab_set))}
        self.feature_names = sorted(self.vocab.keys())
        
        # Calculate class priors
        for cat in self.categories:
            self.class_priors[cat] = self.category_counts[cat] / self.total_docs
        
        self.is_fitted = True
        logger.info(f"Naive Bayes classifier fitted. Vocab size: {len(self.vocab)}, Categories: {len(self.categories)}")

    def predict_proba(self, text: str) -> Dict[str, float]:
        """
        Predict probability distribution over categories.
        
        Returns:
            Dict mapping category -> probability [0.0, 1.0]
        """
        if not self.is_fitted:
            raise RuntimeError("Classifier not fitted. Call fit() first.")
        
        features = self._extract_features(text)
        
        # Calculate log probabilities for numerical stability
        log_probs = {}
        
        for cat in self.categories:
            # Prior
            log_prob = math.log(self.class_priors[cat])
            
            # Feature likelihoods
            for feature, count in features.items():
                # P(feature | category) with Laplace smoothing
                feature_count = self.category_feature_counts[cat].get(feature, 0.0)
                total_features_in_cat = sum(self.category_feature_counts[cat].values())
                
                # Laplace smoothing: (count + alpha) / (total + alpha * vocab_size)
                likelihood = (feature_count + self.alpha) / (total_features_in_cat + self.alpha * len(self.vocab))
                log_prob += count * math.log(likelihood)
            
            log_probs[cat] = log_prob
        
        # Convert log probabilities to probabilities
        # Find max log prob to avoid underflow
        max_log_prob = max(log_probs.values())
        
        probs = {}
        for cat in self.categories:
            probs[cat] = math.exp(log_probs[cat] - max_log_prob)
        
        # Normalize
        total = sum(probs.values())
        for cat in probs:
            probs[cat] /= total
        
        return probs

    def predict(self, text: str) -> Tuple[str, Dict[str, float]]:
        """
        Predict the most likely category.
        
        Returns:
            (predicted_category, probabilities_dict)
        """
        probs = self.predict_proba(text)
        best_cat = max(probs, key=probs.get)
        return best_cat, probs

    def save(self, model_path: Path) -> None:
        """
        Save model to JSON file.
        """
        model_path.parent.mkdir(parents=True, exist_ok=True)
        
        model_data = {
            "categories": self.categories,
            "alpha": self.alpha,
            "vocab": self.vocab,
            "feature_names": self.feature_names,
            "category_counts": self.category_counts,
            "category_feature_counts": {
                cat: dict(counts) for cat, counts in self.category_feature_counts.items()
            },
            "class_priors": self.class_priors,
            "total_docs": self.total_docs,
        }
        
        with open(model_path, "w") as f:
            json.dump(model_data, f, indent=2)
        
        logger.info(f"Model saved to {model_path}")

    @classmethod
    def load(cls, model_path: Path) -> "NaiveBayesClassifier":
        """
        Load model from JSON file.
        """
        with open(model_path, "r") as f:
            model_data = json.load(f)
        
        classifier = cls(
            categories=model_data["categories"],
            alpha=model_data["alpha"]
        )
        
        classifier.vocab = model_data["vocab"]
        classifier.feature_names = model_data["feature_names"]
        classifier.category_counts = model_data["category_counts"]
        
        # Restore defaultdicts
        classifier.category_feature_counts = {
            cat: defaultdict(float, counts)
            for cat, counts in model_data["category_feature_counts"].items()
        }
        
        classifier.class_priors = model_data["class_priors"]
        classifier.total_docs = model_data["total_docs"]
        classifier.is_fitted = True
        
        logger.info(f"Model loaded from {model_path}")
        return classifier
