"""
Light-weight text tokenizer and preprocessor.

Features:
- Lowercase normalization
- Regex-based tokenization
- Stopword filtering
- Simple suffix-stripping stemming (no NLTK)
- Bigram generation
"""

import re
from typing import List, Set, Tuple
from collections import Counter


# Common English stopwords (minimal set to keep content words)
STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "but", "by", "for", "if",
    "in", "into", "is", "it", "no", "not", "of", "on", "or", "such",
    "that", "the", "their", "then", "there", "these", "they", "this",
    "to", "was", "will", "with", "you", "your",
}

# Simple suffix-stripping rules (Porter-like but minimal)
SUFFIX_RULES = [
    ("ies", "i"),      # dependencies -> dependenci
    ("es", ""),        # passes -> pass
    ("s", ""),         # users -> user
    ("ed", ""),        # locked -> lock
    ("ing", ""),       # printing -> print
]

# Text normalization rules: regex patterns to standardize common variations
NORMALIZE_RULES = [
    (r"wi-fi", "wifi"),          # wi-fi -> wifi
    (r"wi\s+fi", "wifi"),        # wi fi -> wifi
    (r"wifi", "wifi"),           # WiFi -> wifi (handled by lowercase)
    (r"e-mail", "email"),        # e-mail -> email
    (r"e\s+mail", "email"),      # e mail -> email
    (r"log-in", "login"),        # log-in -> login
    (r"log\s+in", "login"),      # log in -> login
]


def simple_stem(word: str) -> str:
    """
    Apply simple suffix-stripping rules to shorten word.
    """
    word = word.lower()
    for suffix, replacement in SUFFIX_RULES:
        if word.endswith(suffix):
            return word[:-len(suffix)] + replacement
    return word


def normalize_text(text: str) -> str:
    """
    Normalize text by applying substitution rules.
    Handles variations like: wi-fi/wi fi/WiFi -> wifi, e-mail/e mail -> email, etc.
    
    Args:
        text: Input text
    
    Returns:
        Normalized text
    """
    for pattern, replacement in NORMALIZE_RULES:
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    return text


def tokenize(text: str, remove_stopwords: bool = True, stem: bool = True) -> List[str]:
    """
    Tokenize text into words.
    
    Args:
        text: Input text
        remove_stopwords: Whether to filter out common stopwords
        stem: Whether to apply light stemming
    
    Returns:
        List of processed tokens
    """
    # Lowercase
    text = text.lower()
    
    # Normalize text (e.g., wi-fi -> wifi, e-mail -> email, log-in -> login)
    text = normalize_text(text)
    
    # Split on non-alphanumeric (keep word chars and hyphen)
    tokens = re.findall(r"\b\w+(?:-\w+)?\b", text)
    
    # Remove stopwords
    if remove_stopwords:
        tokens = [t for t in tokens if t not in STOPWORDS]
    
    # Stem
    if stem:
        tokens = [simple_stem(t) for t in tokens]
    
    return tokens


def get_bigrams(tokens: List[str]) -> List[Tuple[str, str]]:
    """Generate consecutive bigrams from tokens."""
    return [(tokens[i], tokens[i+1]) for i in range(len(tokens) - 1)]


def tokenize_with_bigrams(text: str, remove_stopwords: bool = True) -> Tuple[List[str], List[Tuple[str, str]]]:
    """
    Tokenize and return both unigrams and bigrams.
    """
    tokens = tokenize(text, remove_stopwords=remove_stopwords, stem=True)
    bigrams = get_bigrams(tokens) if len(tokens) > 1 else []
    return tokens, bigrams


def get_vocabulary_from_texts(texts: List[str]) -> Set[str]:
    """
    Build vocabulary from a collection of texts.
    Returns set of unique unigrams.
    """
    vocab = set()
    for text in texts:
        tokens = tokenize(text, remove_stopwords=True, stem=True)
        vocab.update(tokens)
    return vocab
