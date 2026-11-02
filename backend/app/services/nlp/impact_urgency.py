"""
Rule-based impact and urgency scoring from message cues.

Detects keywords indicating business impact (everyone, all users, department)
and time sensitivity (urgent, deadline, down, can't work) to determine urgency/impact.

Used alongside deterministic ITIL priority matrix in triage_service.py.
"""

import re
from typing import Tuple


# Cue words indicating HIGH impact (affects many users/systems)
HIGH_IMPACT_CUES = [
    "everyone", "all users", "all staff", "department", "team",
    "entire", "widespread", "company-wide", "organization",
    "multiple", "many", "critical system", "production",
]

# Cue words indicating MEDIUM impact
MEDIUM_IMPACT_CUES = [
    "group", "several", "some users", "some teams",
    "our group", "our department", "my team",
]

# Cue words indicating HIGH urgency (time-sensitive)
HIGH_URGENCY_CUES = [
    "urgent", "asap", "immediately", "can't work", "broken",
    "deadline", "down", "offline", "not working", "emergency",
    "critical", "blocking", "can't use", "unable to", "won't work",
    "stuck", "stopped", "failed", "crash", "hung", "freeze",
    "right now", "this minute", "this second", "immediately",
]

# Cue words indicating MEDIUM urgency
MEDIUM_URGENCY_CUES = [
    "slow", "sluggish", "lag", "issue", "problem",
    "soon", "today", "this morning", "this afternoon",
]

# Cue words indicating LOW urgency
LOW_URGENCY_CUES = [
    "when possible", "no rush", "can wait", "whenever",
    "background", "minor", "cosmetic",
]


def score_impact(message: str) -> str:
    """
    Estimate business impact from message keywords.
    
    Returns:
        "High", "Medium", or "Low"
    """
    lower = message.lower()
    
    # Check for high impact indicators
    for cue in HIGH_IMPACT_CUES:
        if re.search(r"\b" + re.escape(cue) + r"\b", lower):
            return "High"
    
    # Check for medium impact
    for cue in MEDIUM_IMPACT_CUES:
        if re.search(r"\b" + re.escape(cue) + r"\b", lower):
            return "Medium"
    
    return "Low"


def score_urgency(message: str) -> str:
    """
    Estimate time sensitivity from message keywords.
    
    Returns:
        "High", "Medium", or "Low"
    """
    lower = message.lower()
    
    # Check for low urgency first (can override high-seeming words)
    for cue in LOW_URGENCY_CUES:
        if re.search(r"\b" + re.escape(cue) + r"\b", lower):
            return "Low"
    
    # Check for high urgency
    for cue in HIGH_URGENCY_CUES:
        if re.search(r"\b" + re.escape(cue) + r"\b", lower):
            return "High"
    
    # Check for medium urgency
    for cue in MEDIUM_URGENCY_CUES:
        if re.search(r"\b" + re.escape(cue) + r"\b", lower):
            return "Medium"
    
    return "Low"


def score_impact_urgency(message: str) -> Tuple[str, str]:
    """
    Score both impact and urgency from message.
    
    Returns:
        (impact, urgency) tuple
    """
    return score_impact(message), score_urgency(message)
