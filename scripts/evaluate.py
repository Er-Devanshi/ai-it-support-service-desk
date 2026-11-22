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
    misclassified = []
    category_stats = defaultdict(lambda: {"correct": 0, "total": 0})
    
    for query_obj in eval_queries:
        query = query_obj["query"]
        expected_cats = query_obj["expected_categories"]
        
        predicted_cat, probs = classifier.predict(query)
        
        is_correct = predicted_cat in expected_cats
        correct += is_correct
        
        # Track per-category accuracy
        for exp_cat in expected_cats:
            category_stats[exp_cat]["total"] += 1
            if is_correct:
                category_stats[exp_cat]["correct"] += 1
        
        predictions.append({
            "query": query,
            "expected": expected_cats,
            "predicted": predicted_cat,
            "confidence": probs.get(predicted_cat, 0.0),
            "correct": is_correct,
        })
        
        # Track misclassifications
        if not is_correct:
            misclassified.append({
                "query": query,
                "expected": expected_cats[0],
                "predicted": predicted_cat,
                "confidence": probs.get(predicted_cat, 0.0),
            })
    
    accuracy = correct / total if total > 0 else 0.0
    
    return {
        "accuracy": accuracy,
        "correct": correct,
        "total": total,
        "predictions": predictions,
        "misclassified": misclassified,
        "category_accuracy": dict(category_stats),
    }


def evaluate_retriever(retriever, eval_queries):
    """Evaluate retriever on eval queries - measure retrieval correctness against real sources."""
    results = []
    top1_hits = 0
    top3_hits = 0
    failures = []  # Queries where expected source not in top-3
    total_in_scope = 0
    
    for query_obj in eval_queries:
        query = query_obj["query"]
        expected_sources = query_obj["expected_sources"]
        is_kb_gap = query_obj.get("kb_gap", False)
        
        # Skip kb_gap queries from accuracy calculation
        if is_kb_gap:
            continue
        
        total_in_scope += 1
        retrieval_result = retriever.retrieve(query, top_k=5)
        
        # Extract source file names from retrieved documents
        # The source is in format like "account_lockout_guide.md" or similar
        retrieved_sources = []
        retrieved_scores = []
        
        for doc in retrieval_result.documents[:5]:
            # Extract the source filename - it's the most reliable identifier
            source = None
            if hasattr(doc, 'source'):
                source = doc.source
            elif hasattr(doc, 'title'):
                # Try to infer from title if source not available
                title = doc.title.lower()
                # Match KB file names
                for kb_file in ["account_lockout_guide.md", "account_security_guide.md", 
                               "email_outlook_troubleshooting.md", "hardware_printer_troubleshooting.md",
                               "mfa_authentication_guide.md", "sample_it_faq.txt",
                               "slow_computer_performance_guide.md", "software_installation_guide.md",
                               "vpn_remote_access_guide.md", "wifi_wireless_networking_guide.md"]:
                    if kb_file.replace('.md', '').replace('.txt', '').lower() in title:
                        source = kb_file
                        break
            
            if source:
                retrieved_sources.append(source)
                score = doc.relevance_score if hasattr(doc, 'relevance_score') else 0.0
                retrieved_scores.append(score)
        
        # Check if any expected source appears in top-1
        top1_match = False
        if retrieved_sources:
            for expected in expected_sources:
                if retrieved_sources[0] == expected:
                    top1_match = True
                    break
        
        # Check if any expected source appears in top-3
        top3_match = False
        for idx in range(min(3, len(retrieved_sources))):
            for expected in expected_sources:
                if retrieved_sources[idx] == expected:
                    top3_match = True
                    break
        
        if top1_match:
            top1_hits += 1
        if top3_match:
            top3_hits += 1
        
        # Record for detailed analysis
        result_obj = {
            "query": query,
            "expected_sources": expected_sources,
            "top1_match": top1_match,
            "top3_match": top3_match,
            "retrieved_sources": retrieved_sources[:3],
            "retrieved_scores": retrieved_scores[:3],
            "top_score": retrieved_scores[0] if retrieved_scores else 0.0,
        }
        
        results.append(result_obj)
        
        # Track failures
        if not top3_match and expected_sources:  # Only report if KB had answer
            # Capture first 2 lines of retrieved content for analysis
            top3_with_preview = []
            for i in range(min(3, len(retrieval_result.documents))):
                doc = retrieval_result.documents[i]
                content_lines = doc.content.strip().split('\n')[:2] if doc.content else [""]
                preview = " ".join([line.strip() for line in content_lines])[:100]
                top3_with_preview.append({
                    "source": retrieved_sources[i] if i < len(retrieved_sources) else "unknown",
                    "score": retrieved_scores[i] if i < len(retrieved_scores) else 0.0,
                    "preview": preview,
                })
            
            failures.append({
                "query": query,
                "expected_sources": expected_sources,
                "top3_retrieved": top3_with_preview,
            })
    
    top1_rate = (top1_hits / total_in_scope * 100) if total_in_scope > 0 else 0.0
    top3_rate = (top3_hits / total_in_scope * 100) if total_in_scope > 0 else 0.0
    
    return {
        "total_in_scope": total_in_scope,
        "total_queries": len(eval_queries),
        "top1_hits": top1_hits,
        "top1_hit_rate": top1_rate,
        "top3_hits": top3_hits,
        "top3_hit_rate": top3_rate,
        "failures": failures,
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


def generate_report(classifier_eval, retriever_eval, e2e_eval, eval_queries, output_file: Path):
    """Generate evaluation report."""
    report = {
        "title": "ServiceDesk-AI NLP Engine Evaluation Report",
        "timestamp": str(Path(__file__).stat().st_mtime),
        "classifier": classifier_eval,
        "retriever": retriever_eval,
        "end_to_end": e2e_eval,
        "summary": {
            "classifier_accuracy": f"{classifier_eval['accuracy']*100:.1f}%",
            "classifier_misclassified": len(classifier_eval.get('misclassified', [])),
            "retriever_in_scope": retriever_eval.get('total_in_scope', 0),
            "retriever_top1_hit_rate": f"{retriever_eval.get('top1_hit_rate', 0):.1f}%",
            "retriever_top3_hit_rate": f"{retriever_eval.get('top3_hit_rate', 0):.1f}%",
            "retriever_failures": len(retriever_eval.get('failures', [])),
            "kb_gaps": len([q for q in eval_queries if q.get('kb_gap', False)]),
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
    print("=" * 70)
    
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
    print(f"   BM25 index written to: data/index/bm25.json (rebuilt on each run)")
    
    # Load eval queries
    print("\n3. Loading evaluation queries...")
    eval_file = Path(__file__).parent.parent / "data" / "eval" / "retrieval_queries.json"
    eval_queries = load_eval_queries(eval_file)
    print(f"   Loaded {len(eval_queries)} evaluation queries")
    
    # Run evaluations
    print("\n4. Running classifier evaluation...")
    classifier_eval = evaluate_classifier(classifier, eval_queries)
    print(f"   Overall accuracy: {classifier_eval['accuracy']*100:.1f}% ({classifier_eval['correct']}/{classifier_eval['total']})")
    
    # Print per-category accuracy
    print("\n   Per-category accuracy:")
    for category in sorted(classifier_eval['category_accuracy'].keys()):
        cat_stats = classifier_eval['category_accuracy'][category]
        cat_acc = cat_stats['correct'] / cat_stats['total'] * 100 if cat_stats['total'] > 0 else 0
        print(f"     {category:12s}: {cat_acc:5.1f}% ({cat_stats['correct']}/{cat_stats['total']})")
    
    # Print misclassified queries
    if classifier_eval['misclassified']:
        print(f"\n   Misclassified queries ({len(classifier_eval['misclassified'])}):")
        for mc in classifier_eval['misclassified'][:10]:  # Show first 10
            print(f"     {mc['query'][:60]:60s} | expected: {mc['expected']:12s} | predicted: {mc['predicted']:12s} | conf: {mc['confidence']:.3f}")
        if len(classifier_eval['misclassified']) > 10:
            print(f"     ... and {len(classifier_eval['misclassified']) - 10} more")
    
    print("\n5. Running retriever evaluation...")
    retriever_eval = evaluate_retriever(retriever, eval_queries)
    print(f"   Top-1 hit rate (in-scope): {retriever_eval['top1_hit_rate']:.1f}% ({retriever_eval['top1_hits']}/{retriever_eval['total_in_scope']})")
    print(f"   Top-3 hit rate (in-scope): {retriever_eval['top3_hit_rate']:.1f}% ({retriever_eval['top3_hits']}/{retriever_eval['total_in_scope']})")
    
    # Print retrieval failures
    if retriever_eval['failures']:
        print(f"\n   Retrieval failures (expected source not in top-3) ({len(retriever_eval['failures'])}):")
        for failure in retriever_eval['failures']:
            print(f"     Query: {failure['query'][:70]}")
            print(f"       Expected: {', '.join(failure['expected_sources'])}")
            for i, r in enumerate(failure['top3_retrieved'][:2], 1):
                preview = r.get('preview', '')[:80]
                print(f"       [{i}] {r['source']} ({r['score']:.3f}): {preview}...")
        if len(retriever_eval['failures']) > 10:
            print(f"     ... and {len(retriever_eval['failures']) - 10} more retrieval failures")
    
    # Identify kb_gap queries
    kb_gap_queries = [q for q in eval_queries if q.get("kb_gap", False)]
    if kb_gap_queries:
        print(f"\n   Knowledge base gaps ({len(kb_gap_queries)} queries with no KB coverage):")
        gaps_by_topic = {}
        for q in kb_gap_queries:
            category = q["expected_categories"][0] if q["expected_categories"] else "general"
            if category not in gaps_by_topic:
                gaps_by_topic[category] = []
            gaps_by_topic[category].append(q["query"])
        
        for category in sorted(gaps_by_topic.keys()):
            print(f"     {category.upper()}:")
            for query in gaps_by_topic[category][:5]:
                print(f"       - {query}")
            if len(gaps_by_topic[category]) > 5:
                print(f"       ... and {len(gaps_by_topic[category]) - 5} more")
    
    print("\n6. Confidence gating check...")
    conf_threshold = getattr(settings, 'RAG_STRONG_MATCH_THRESHOLD', 0.5)
    conf_file = "backend/app/config.py"
    conf_config = "RAG_STRONG_MATCH_THRESHOLD"
    print(f"   Threshold defined in: {conf_file}")
    print(f"   Config setting: {conf_config} = {conf_threshold}")
    # Count queries with top score below threshold (would be escalated)
    below_threshold = sum(1 for r in retriever_eval['queries'] if r['top_score'] < conf_threshold)
    print(f"   Queries below threshold: {below_threshold}/{len(retriever_eval['queries'])}")
    
    print("\n7. Running end-to-end evaluation...")
    e2e_eval = evaluate_end_to_end(classifier, retriever, eval_queries)
    print(f"   Classification accuracy: {e2e_eval['classification_accuracy']*100:.1f}%")
    print(f"   Retrieval success: {e2e_eval['retrieval_success_rate']*100:.1f}%")
    print(f"   Escalation rate: {e2e_eval['escalation_rate']*100:.1f}%")
    print(f"   Escalation explanation:")
    print(f"   - escalation_rate is 0% because build_response() doesn't use confidence gating")
    print(f"   - Escalation only triggers on special cases (security, urgent), not on low confidence scores")
    
    # Generate report
    print("\n8. Generating report...")
    report_file = Path(__file__).parent.parent / "reports" / "evaluation_results.json"
    report = generate_report(classifier_eval, retriever_eval, e2e_eval, eval_queries, report_file)
    print(f"   Report saved to: {report_file}")
    
    print("\n" + "=" * 70)
    print("Evaluation complete!")
    print("\nSummary:")
    for key, value in report["summary"].items():
        print(f"  {key}: {value}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
