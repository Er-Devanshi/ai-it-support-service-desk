"""
Intent Engine Evaluation Script — ServiceDesk-AI.

Evaluates on data/intent_eval.json (held-out, never used for training).
Prints:
  1. Overall accuracy and per-intent accuracy
  2. Full list of misclassified queries
  3. End-to-end routing check on 15 messages (security / greeting / ticket / technical)

Usage:
    python scripts/eval_intent.py
    (run from repo root; .venv must be activated)
"""

import sys
import json
from pathlib import Path
from collections import defaultdict

# Make backend importable when running from repo root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from app.services.intent_engine.intent_classifier import classify
from app.services.intent_engine.router import route_intent
from app.config import settings

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parent.parent
EVAL_PATH = REPO_ROOT / "data" / "intent_eval.json"

# ---------------------------------------------------------------------------
# 1. Classification accuracy on held-out eval set
# ---------------------------------------------------------------------------

def evaluate_classification():
    print("=" * 60)
    print("INTENT CLASSIFICATION EVALUATION")
    print(f"Eval file : {EVAL_PATH}")
    print("=" * 60)

    with open(EVAL_PATH, encoding="utf-8") as f:
        eval_data = json.load(f)

    total = len(eval_data)
    correct = 0
    per_intent_total = defaultdict(int)
    per_intent_correct = defaultdict(int)
    misclassified = []

    for item in eval_data:
        query = item["query"]
        expected = item["intent"]
        predicted, confidence = classify(query)

        per_intent_total[expected] += 1
        if predicted == expected:
            correct += 1
            per_intent_correct[expected] += 1
        else:
            misclassified.append({
                "query": query,
                "expected": expected,
                "predicted": predicted,
                "confidence": round(confidence, 3),
            })

    overall_acc = correct / total if total > 0 else 0.0
    print(f"\nOverall accuracy : {correct}/{total} = {overall_acc:.1%}\n")

    print("Per-intent accuracy:")
    for intent in sorted(per_intent_total.keys()):
        t = per_intent_total[intent]
        c = per_intent_correct[intent]
        acc = c / t if t > 0 else 0.0
        print(f"  {intent:<25} {c:2}/{t:2}  ({acc:.0%})")

    if misclassified:
        print(f"\nMisclassified ({len(misclassified)}):")
        for m in misclassified:
            print(
                f"  [{m['expected']} -> {m['predicted']} conf={m['confidence']}]  \"{m['query']}\""
            )
    else:
        print("\nNo misclassifications.")

    return overall_acc


# ---------------------------------------------------------------------------
# 2. End-to-end routing check (15 hand-picked messages)
# ---------------------------------------------------------------------------

ROUTING_CASES = [
    # (message, description)
    ("Help, my account was hacked",             "SECURITY: should go to security_escalation"),
    ("Our files are encrypted by ransomware",    "SECURITY: P1 escalation"),
    ("Hello",                                    "GREETING: short, no tech -> handled directly"),
    ("Hi",                                       "GREETING: short, no tech -> handled directly"),
    ("Thanks",                                   "THANKS:   short, no tech -> handled directly"),
    ("Goodbye",                                  "GOODBYE:  short, no tech -> handled directly"),
    ("hi, my VPN is down",                       "TRICKY: greeting+tech -> pipeline (troubleshoot)"),
    ("thanks but wifi still not working",        "TRICKY: thanks+tech -> pipeline (troubleshoot)"),
    ("Show me my tickets",                       "CHECK_TICKET_STATUS -> handler (if confident)"),
    ("Please create a ticket",                   "CREATE_TICKET -> handler (if confident)"),
    ("My laptop is running very slowly",         "TROUBLESHOOT -> pipeline"),
    ("The printer is offline",                   "TROUBLESHOOT -> pipeline"),
    ("I cannot connect to the VPN",              "TROUBLESHOOT -> pipeline"),
    ("My password expired and I cannot log in",  "TROUBLESHOOT -> pipeline"),
    ("Outlook is not syncing my emails",         "TROUBLESHOOT -> pipeline"),
]


def evaluate_routing():
    print("\n" + "=" * 60)
    print("END-TO-END ROUTING CHECK (USE_INTENT=True)")
    print("=" * 60)
    # Enable intent layer for this check
    settings.USE_INTENT = True

    print(f"{'Message':<44} {'Intent':<22} {'Conf':>5}  {'Route':<22} {'Note'}")
    print("-" * 120)
    for msg, note in ROUTING_CASES:
        intent, conf, target = route_intent(msg, {})
        print(
            f"  {msg[:42]:<42}  {intent:<22} {conf:>5.2f}  {target:<22} {note}"
        )

    # Restore default
    settings.USE_INTENT = False


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    acc = evaluate_classification()
    evaluate_routing()
    print("\nDone.")
    # Exit 0 always (non-zero exit reserved for hard failures)
    sys.exit(0)
