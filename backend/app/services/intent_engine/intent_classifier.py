"""
Intent Classifier for ServiceDesk-AI.

Wraps the existing NaiveBayesClassifier (from app.services.nlp.classifier)
and trains it on data/intents.json.  No external ML libraries are used.

Intents:
  greeting, thanks, goodbye, check_ticket_status, create_ticket, troubleshoot

The classifier is trained once at import time and cached as a module-level
singleton. Training is fast (< 0.1 s on the 130-example dataset).
"""

import json
from pathlib import Path
from typing import Tuple

from app.services.nlp.classifier import NaiveBayesClassifier
from app.utils.logger import logger

# Path to training data
_INTENTS_PATH = Path(__file__).resolve().parent.parent.parent.parent.parent / "data" / "intents.json"

# Singleton trained classifier (loaded once)
_intent_classifier: NaiveBayesClassifier | None = None


def _load_training_data(path: Path) -> Tuple[list, list]:
    """
    Load intents.json and return (texts, labels) lists for training.

    intents.json format:
      { "intents": { "greeting": ["Hello", ...], "troubleshoot": [...], ... } }
    """
    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    texts, labels = [], []
    for intent, examples in data["intents"].items():
        for text in examples:
            texts.append(text)
            labels.append(intent)
    return texts, labels


def _get_classifier() -> NaiveBayesClassifier:
    """Return the singleton intent classifier, training it on first call."""
    global _intent_classifier
    if _intent_classifier is not None:
        return _intent_classifier

    if not _INTENTS_PATH.exists():
        raise FileNotFoundError(
            f"Intent training data not found at {_INTENTS_PATH}. "
            "Expected data/intents.json relative to the repo root."
        )

    texts, labels = _load_training_data(_INTENTS_PATH)
    clf = NaiveBayesClassifier()
    clf.fit(texts, labels)
    _intent_classifier = clf
    logger.info(
        f"[IntentClassifier] Trained on {len(texts)} examples, "
        f"intents: {clf.categories}"
    )
    return clf


def classify(message: str) -> Tuple[str, float]:
    """
    Classify a message into one of the 6 intents.

    Returns:
        (intent_label, confidence)  e.g. ("greeting", 0.91)
    """
    clf = _get_classifier()
    intent, probs = clf.predict(message)
    confidence = probs[intent]
    return intent, confidence


def reset_classifier() -> None:
    """Force re-train on next call. Useful in tests."""
    global _intent_classifier
    _intent_classifier = None
