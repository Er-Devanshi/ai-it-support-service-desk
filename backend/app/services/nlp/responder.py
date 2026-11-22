"""
Extractive responder: builds responses from retrieved knowledge chunks.

Never invents or hallucinates content. Extracts only real steps (numbered/bulleted items)
from retrieved docs, joined as clean prose. Never includes metadata lines like CATEGORY:, Title:, etc.

If no documents meet the relevance threshold, suggests ticket creation/escalation.
"""

import re
from typing import List, Dict, Optional, Tuple

from app.services.rag.retrieval_interface import RetrievedChunk
from app.config import settings
from app.utils.logger import logger


def extract_steps_from_content(text: str) -> List[str]:
    """
    Extract ONLY real steps (numbered or bulleted items, preferably under a Steps/Solution heading).
    Skip metadata lines (Title:, CATEGORY:, Topic:, PROBLEM:, etc.).
    Join wrapped continuations of the same sentence.
    
    Returns:
        List of clean step texts (deduplicated, no metadata)
    """
    lines = text.split("\n")
    steps = []
    in_steps_section = False
    current_step = ""
    
    # Metadata patterns to skip
    metadata_patterns = [
        r"^(Title|TITLE|Topic|TOPIC|CATEGORY|Category|PROBLEM|Problem|Description):\s*",
        r"^FAQ\s+\d+",
        r"^---",
    ]
    
    for line in lines:
        original_line = line
        line = line.strip()
        
        # Skip empty lines
        if not line:
            if current_step:
                steps.append(current_step.strip())
                current_step = ""
            in_steps_section = False
            continue
        
        # Check for "Steps" or "Solution" or "Resolution" section headers
        if re.match(r"^(Steps|Solution|Resolution|Troubleshooting|How to)s?", line, re.IGNORECASE):
            in_steps_section = True
            if current_step:
                steps.append(current_step.strip())
                current_step = ""
            continue
        
        # Skip metadata lines
        is_metadata = False
        for pattern in metadata_patterns:
            if re.match(pattern, line):
                is_metadata = True
                break
        
        if is_metadata:
            if current_step:
                steps.append(current_step.strip())
                current_step = ""
            in_steps_section = False
            continue
        
        # Check if line is a numbered/bulleted step
        step_match = re.match(r"^[\d]+[\.\)]\s+(.+)$|^[•\-\*]\s+(.+)$", line)
        
        if step_match:
            # New step found
            if current_step:
                steps.append(current_step.strip())
            step_text = step_match.group(1) or step_match.group(2)
            current_step = step_text
        elif current_step and (in_steps_section or steps):
            # Continuation of previous step (wrapped line)
            current_step += " " + line
        elif in_steps_section and len(line) > 10:
            # In a steps section and this looks like prose -> treat as step
            if current_step:
                steps.append(current_step.strip())
            current_step = line
    
    # Add final step
    if current_step:
        steps.append(current_step.strip())
    
    return steps


def build_response(
    category: str,
    retrieved_docs: List[RetrievedChunk],
    relevance_threshold: float = settings.RAG_RELEVANCE_THRESHOLD,
) -> Tuple[str, bool]:
    """
    Build an extractive response from retrieved chunks.
    
    Args:
        category: Issue category (for filtering)
        retrieved_docs: List of RetrievedChunk from retriever
        relevance_threshold: Minimum relevance score to use
    
    Returns:
        (response_text, should_escalate)
        - response_text: The formatted response (intro + extracted steps + Source line)
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
    
    # Build intro from document title (not category)
    intro = f"Here is the guide: {doc.title}"
    
    # Extract steps from content
    steps = extract_steps_from_content(doc.content)
    
    if not steps:
        # No steps found, use first 3 sentences of content
        sentences = re.split(r'(?<=[.!?])\s+', doc.content)[:3]
        content_snippet = ' '.join(sentences)
        response = f"{intro}\n\n{content_snippet}"
    else:
        # Format steps
        response = intro + "\n"
        for step in steps:
            response += f"\n• {step}"
    
    # Add Source line (REQUIRED)
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
