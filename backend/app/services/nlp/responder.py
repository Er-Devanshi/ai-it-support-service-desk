"""
Extractive responder: builds responses from retrieved knowledge chunks.

Never invents or hallucinates content. Extracts numbered steps from retrieved docs
and formats with category-specific introductions.

If no documents meet the relevance threshold, suggests ticket creation/escalation.
"""

import re
from typing import List, Dict, Optional, Tuple

from app.services.rag.retrieval_interface import RetrievedChunk
from app.config import settings
from app.utils.logger import logger


# Category-specific response templates (introductions only; body is extracted)
CATEGORY_INTROS = {
    "network": "Here are the troubleshooting steps for network connectivity issues:\n",
    "account": "Here's how to resolve account access problems:\n",
    "security": "Here are steps to secure your account:\n",
    "hardware": "Here are hardware troubleshooting steps:\n",
    "software": "Here's how to handle software installation:\n",
    "email": "Here's how to resolve email issues:\n",
    "performance": "Here are steps to improve system performance:\n",
    "general": "Here's assistance for your IT issue:\n",
}


def extract_steps(text: str) -> List[str]:
    """
    Extract numbered steps from text (e.g., "1. step 1", "2. step 2").
    
    Returns:
        List of step texts (with or without numbers removed, clean)
    """
    # Pattern: "1. text", "1) text", "• text", "- text"
    patterns = [
        r"^\d+[\.\)]\s+(.+)$",  # Numbered
        r"^[•\-\*]\s+(.+)$",    # Bullets
    ]
    
    steps = []
    for line in text.split("\n"):
        line = line.strip()
        if not line:
            continue
        
        for pattern in patterns:
            match = re.match(pattern, line)
            if match:
                steps.append(match.group(1) if match.groups() else line)
                break
        else:
            # No pattern match, keep line as-is if it looks like a step
            if len(line) > 10:  # Filter out very short lines
                steps.append(line)
    
    return steps


def build_response(
    category: str,
    retrieved_docs: List[RetrievedChunk],
    relevance_threshold: float = settings.RAG_RELEVANCE_THRESHOLD,
) -> Tuple[str, bool]:
    """
    Build an extractive response from retrieved chunks.
    
    Args:
        category: Issue category (for intro template)
        retrieved_docs: List of RetrievedChunk from retriever
        relevance_threshold: Minimum relevance score to use
    
    Returns:
        (response_text, should_escalate)
        - response_text: The formatted response (or escalation message)
        - should_escalate: True if no good docs were found
    """
    
    # Filter by relevance
    good_docs = [
        doc for doc in retrieved_docs
        if doc.relevance_score is not None and doc.relevance_score >= relevance_threshold
    ]
    
    if not good_docs:
        # No documents above threshold -> suggest ticket
        return (
            "I was unable to find matching solutions in the knowledge base for your issue.\n\n"
            "Please create a support ticket so our IT team can assist you further.",
            True,  # escalate
        )
    
    # Build response from first good doc (most relevant)
    doc = good_docs[0]
    
    # Get intro
    intro = CATEGORY_INTROS.get(category, CATEGORY_INTROS["general"])
    
    # Extract steps from content
    steps = extract_steps(doc.content)
    
    if not steps:
        # No steps found in content, use raw content (capped)
        content_snippet = doc.content[:300]
        if len(doc.content) > 300:
            content_snippet += "..."
        response = f"{intro}\n{content_snippet}"
    else:
        # Format steps
        response = intro
        for i, step in enumerate(steps, 1):
            response += f"\n{i}. {step}"
    
    # Add citation
    response += f"\n\n**Source:** {doc.title}"
    
    return response, False  # no escalation needed


def build_escalation_response(reason: Optional[str] = None) -> str:
    """
    Build a response when escalation is required (no knowledge base match).
    """
    msg = "I was unable to resolve your issue automatically.\n\n"
    if reason:
        msg += f"Reason: {reason}\n\n"
    msg += "A support ticket will be created for you, and our IT team will assist shortly."
    return msg
