"""
Train the Naive Bayes classifier on labeled ticket data.

Outputs:
- Model saved to data/models/classifier.json
- Metrics: accuracy, per-class precision/recall/F1
- Confusion matrix
- Train/test split: 80/20 (seeded for reproducibility)
"""

import sys
import csv
from pathlib import Path
from collections import Counter

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.services.nlp.classifier import NaiveBayesClassifier
from app.utils.logger import logger


def load_training_data(csv_path: Path):
    """Load ticket CSV into lists of texts and labels."""
    texts = []
    labels_category = []
    
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            texts.append(row["text"].strip())
            labels_category.append(row["category"].strip())
    
    return texts, labels_category


def train_test_split(texts, labels, test_size=0.2, seed=42):
    """Simple deterministic train/test split."""
    import random
    random.seed(seed)
    
    indices = list(range(len(texts)))
    random.shuffle(indices)
    
    split_idx = int(len(texts) * (1 - test_size))
    train_indices = indices[:split_idx]
    test_indices = indices[split_idx:]
    
    train_texts = [texts[i] for i in train_indices]
    train_labels = [labels[i] for i in train_indices]
    test_texts = [texts[i] for i in test_indices]
    test_labels = [labels[i] for i in test_indices]
    
    return train_texts, train_labels, test_texts, test_labels


def compute_metrics(classifier, texts, labels):
    """Compute accuracy, precision, recall, F1 per category."""
    predictions = [classifier.predict(text)[0] for text in texts]
    
    categories = set(labels)
    
    # Overall accuracy
    correct = sum(1 for pred, true in zip(predictions, labels) if pred == true)
    accuracy = correct / len(labels) if labels else 0.0
    
    # Per-category metrics
    per_class = {}
    for cat in sorted(categories):
        tp = sum(1 for pred, true in zip(predictions, labels) if pred == cat and true == cat)
        fp = sum(1 for pred, true in zip(predictions, labels) if pred == cat and true != cat)
        fn = sum(1 for pred, true in zip(predictions, labels) if pred != cat and true == cat)
        
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
        
        per_class[cat] = {
            "precision": round(precision, 3),
            "recall": round(recall, 3),
            "f1": round(f1, 3),
            "support": sum(1 for true in labels if true == cat),
        }
    
    return {
        "accuracy": round(accuracy, 3),
        "per_class": per_class,
        "predictions": predictions,
    }


def confusion_matrix(true_labels, pred_labels):
    """Build simple confusion matrix."""
    categories = sorted(set(true_labels) | set(pred_labels))
    
    matrix = {cat: {c: 0 for c in categories} for cat in categories}
    for true, pred in zip(true_labels, pred_labels):
        matrix[true][pred] += 1
    
    return matrix, categories


def main():
    # Paths
    data_dir = Path(__file__).parent.parent / "data"
    training_file = data_dir / "training" / "tickets.csv"
    model_dir = data_dir / "models"
    model_path = model_dir / "classifier.json"
    
    if not training_file.exists():
        logger.error(f"Training file not found: {training_file}")
        return 1
    
    # Load data
    logger.info(f"Loading training data from {training_file}...")
    texts, labels = load_training_data(training_file)
    logger.info(f"Loaded {len(texts)} samples")
    
    # Check label distribution
    label_dist = Counter(labels)
    logger.info(f"Label distribution: {dict(label_dist)}")
    
    # Split
    logger.info("Splitting 80/20 train/test (seeded)...")
    train_texts, train_labels, test_texts, test_labels = train_test_split(
        texts, labels, test_size=0.2, seed=42
    )
    logger.info(f"Train: {len(train_texts)}, Test: {len(test_texts)}")
    
    # Train
    logger.info("Training Naive Bayes classifier...")
    classifier = NaiveBayesClassifier(alpha=1.0)
    classifier.fit(train_texts, train_labels)
    logger.info(f"Fitted on {classifier.total_docs} docs with {len(classifier.vocab)} features")
    
    # Evaluate
    logger.info("Evaluating on test set...")
    test_metrics = compute_metrics(classifier, test_texts, test_labels)
    
    logger.info(f"Test Accuracy: {test_metrics['accuracy']}")
    logger.info("Per-class metrics:")
    for cat, metrics in sorted(test_metrics["per_class"].items()):
        logger.info(f"  {cat}: P={metrics['precision']}, R={metrics['recall']}, F1={metrics['f1']} (n={metrics['support']})")
    
    # Confusion matrix
    conf_mat, cats = confusion_matrix(test_labels, test_metrics["predictions"])
    logger.info("Confusion matrix:")
    logger.info("Pred/True: " + ", ".join(f"{c:12}" for c in cats))
    for true_cat in cats:
        row = ", ".join(f"{conf_mat[true_cat][pred]:12}" for pred in cats)
        logger.info(f"{true_cat:12}: {row}")
    
    # Save model
    logger.info(f"Saving model to {model_path}...")
    classifier.save(model_path)
    
    # Summary
    print("\n" + "="*60)
    print("TRAINING SUMMARY")
    print("="*60)
    print(f"Training samples: {len(train_texts)}")
    print(f"Test samples: {len(test_texts)}")
    print(f"Vocabulary size: {len(classifier.vocab)}")
    print(f"Categories: {len(classifier.categories)}")
    print(f"Test Accuracy: {test_metrics['accuracy']}")
    print(f"Model saved: {model_path}")
    print("="*60 + "\n")
    
    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
