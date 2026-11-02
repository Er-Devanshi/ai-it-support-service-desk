#!/usr/bin/env python
"""
Evaluate NLP engine performance on retrieval and classification tasks.

Generates comprehensive evaluation metrics:
- Classifier accuracy on eval queries
- BM25 retrieval relevance
- Response generation quality
- End-to-end system accuracy
"""

import sys
import os
import json
from pathlib import Path
from collections import defaultdict

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.services.nlp.classifier import NaiveBayesClassifier
from app.services.nlp.retriever import BM25Retriever
from app.services.nlp.responder import build_response
from app.services.rag.document_loader import load_knowledge_base_dir
from app.services.rag.chunker import DocumentChunker
from app.config import settings


def load_eval_queries(eval_file: Path):
    """Load evaluation query set."""
    with open(eval_file, "r") as f:
        return json.load(f)


def evaluate_classifier(classifier, eval_queries):
    """Evaluate classifier on eval queries."""
    correct = 0
    total = len(eval_queries)
    predictions = []
    
    for query_obj in eval_queries:
        query = query_obj["query"]
        expected_cats = query_obj["expected_categories"]
        
        predicted_cat, probs = classifier.predict(query)
        
        is_correct = predicted_cat in expected_cats
        correct += is_correct
        
        predictions.append({
            "query": query,
            "expected": expected_cats,
            "predicted": predicted_cat,
            "confidence": probs.get(predicted_cat, 0.0),
            "correct": is_correct,
        })
    
    accuracy = correct / total if total > 0 else 0.0
    
    return {
        "accuracy": accuracy,
        "correct": correct,
        "total": total,
        "predictions": predictions,
    }


def evaluate_retriever(retriever, eval_queries):
    """Evaluate retriever on eval queries."""
    results = []
    
    for query_obj in eval_queries:
        query = query_obj["query"]
        
        retrieval_result = retriever.retrieve(query, top_k=5)
        
        results.append({
            "query": query,
            "num_retrieved": len(retrieval_result.documents),
            "top_score": retrieval_result.documents[0].relevance_score if retrieval_result.documents else 0.0,
            "provider": retrieval_result.provider_info,
            "is_available": retrieval_result.is_available,
        })
    
    available_count = sum(1 for r in results if r["is_available"])
    avg_retrieved = sum(r["num_retrieved"] for r in results) / len(results) if results else 0
    avg_score = sum(r["top_score"] for r in results) / len(results) if results else 0.0
    
    return {
        "total_queries": len(results),
        "available_count": available_count,
        "avg_retrieved": avg_retrieved,
        "avg_top_score": avg_score,
        "queries": results,
    }


def evaluate_end_to_end(classifier, retriever, eval_queries):
    """Evaluate end-to-end query -> classification -> retrieval."""
    results = []
    
    for query_obj in eval_queries:
        query = query_obj["query"]
        expected_category = query_obj["expected_categories"][0]  # Primary category
        
        # Classify
        predicted_cat, cat_probs = classifier.predict(query)
        cat_correct = predicted_cat in query_obj["expected_categories"]
        
        # Retrieve
        retrieval_result = retriever.retrieve(query, top_k=3)
        retrieved_successfully = len(retrieval_result.documents) > 0
        
        # Build response
        response, should_escalate = build_response(
            category=predicted_cat,
            retrieved_docs=retrieval_result.documents,
            relevance_threshold=settings.RAG_RELEVANCE_THRESHOLD,
        )
        
        results.append({
            "query": query,
            "classification": {
                "predicted": predicted_cat,
                "expected": expected_category,
                "correct": cat_correct,
                "confidence": cat_probs.get(predicted_cat, 0.0),
            },
            "retrieval": {
                "retrieved_count": len(retrieval_result.documents),
                "top_score": retrieval_result.documents[0].relevance_score if retrieval_result.documents else 0.0,
                "success": retrieved_successfully,
            },
            "response": {
                "length": len(response),
                "escalated": should_escalate,
            },
        })
    
    classification_acc = sum(1 for r in results if r["classification"]["correct"]) / len(results)
    retrieval_success = sum(1 for r in results if r["retrieval"]["success"]) / len(results)
    escalation_rate = sum(1 for r in results if r["response"]["escalated"]) / len(results)
    
    return {
        "total_queries": len(results),
        "classification_accuracy": classification_acc,
        "retrieval_success_rate": retrieval_success,
        "escalation_rate": escalation_rate,
        "queries": results,
    }


def generate_report(classifier_eval, retriever_eval, e2e_eval, output_file: Path):
    """Generate evaluation report."""
    report = {
        "title": "ServiceDesk-AI NLP Engine Evaluation Report",
        "timestamp": str(Path(__file__).stat().st_mtime),
        "classifier": classifier_eval,
        "retriever": retriever_eval,
        "end_to_end": e2e_eval,
        "summary": {
            "classifier_accuracy": f"{classifier_eval['accuracy']*100:.1f}%",
            "retriever_avg_score": f"{retriever_eval['avg_top_score']:.3f}",
            "e2e_classification_accuracy": f"{e2e_eval['classification_accuracy']*100:.1f}%",
            "e2e_retrieval_success": f"{e2e_eval['retrieval_success_rate']*100:.1f}%",
            "escalation_rate": f"{e2e_eval['escalation_rate']*100:.1f}%",
        },
    }
    
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w") as f:
        json.dump(report, f, indent=2)
    
    return report


def main():
    """Run evaluation."""
    print("ServiceDesk-AI NLP Engine Evaluation")
    print("=" * 50)
    
    # Load classifier
    print("\n1. Loading classifier...")
    classifier_path = Path(__file__).parent.parent / "data" / "models" / "classifier.json"
    if not classifier_path.exists():
        print(f"ERROR: Classifier not found at {classifier_path}")
        print("Run: python scripts/train_classifier.py first")
        return 1
    
    classifier = NaiveBayesClassifier.load(classifier_path)
    print(f"   Loaded classifier with {len(classifier.categories)} categories")
    
    # Setup retriever
    print("\n2. Setting up retriever...")
    index_path = Path(__file__).parent.parent / "data" / "index"
    retriever = BM25Retriever(index_path=index_path / "bm25.json")
    
    # Load and index knowledge base
    print("   Loading knowledge base...")
    docs = load_knowledge_base_dir(settings.KNOWLEDGE_BASE_DIR)
    print(f"   Loaded {len(docs)} documents")
    
    chunker = DocumentChunker()
    chunks = []
    for doc in docs:
        doc_chunks = chunker.chunk_document(doc)
        chunks.extend(doc_chunks)
    print(f"   Created {len(chunks)} chunks")
    
    # Convert chunks to documents for BM25
    bm25_docs = [
        {
            "id": chunk.chunk_id,
            "title": chunk.title,
            "content": chunk.content,
            "source": chunk.source,
            "metadata": chunk.metadata or {},
        }
        for chunk in chunks
    ]
    
    retriever.rebuild_from_documents(bm25_docs)
    print(f"   Indexed {len(bm25_docs)} documents in BM25")
    
    # Load eval queries
    print("\n3. Loading evaluation queries...")
    eval_file = Path(__file__).parent.parent / "data" / "eval" / "retrieval_queries.json"
    eval_queries = load_eval_queries(eval_file)
    print(f"   Loaded {len(eval_queries)} evaluation queries")
    
    # Run evaluations
    print("\n4. Running classifier evaluation...")
    classifier_eval = evaluate_classifier(classifier, eval_queries)
    print(f"   Accuracy: {classifier_eval['accuracy']*100:.1f}% ({classifier_eval['correct']}/{classifier_eval['total']})")
    
    print("\n5. Running retriever evaluation...")
    retriever_eval = evaluate_retriever(retriever, eval_queries)
    print(f"   Available: {retriever_eval['available_count']}/{retriever_eval['total_queries']}")
    print(f"   Avg retrieved: {retriever_eval['avg_retrieved']:.1f} docs")
    print(f"   Avg top score: {retriever_eval['avg_top_score']:.3f}")
    
    print("\n6. Running end-to-end evaluation...")
    e2e_eval = evaluate_end_to_end(classifier, retriever, eval_queries)
    print(f"   Classification accuracy: {e2e_eval['classification_accuracy']*100:.1f}%")
    print(f"   Retrieval success: {e2e_eval['retrieval_success_rate']*100:.1f}%")
    print(f"   Escalation rate: {e2e_eval['escalation_rate']*100:.1f}%")
    
    # Generate report
    print("\n7. Generating report...")
    report_file = Path(__file__).parent.parent / "reports" / "evaluation_results.json"
    report = generate_report(classifier_eval, retriever_eval, e2e_eval, report_file)
    print(f"   Report saved to {report_file}")
    
    print("\n" + "=" * 50)
    print("Evaluation complete!")
    print("\nSummary:")
    for key, value in report["summary"].items():
        print(f"  {key}: {value}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
