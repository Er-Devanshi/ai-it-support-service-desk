"""
Dedicated AI Ticket Triage and Prioritization Service for ServiceDesk-AI.

Implements:
- Category & subcategory classification (via Naive Bayes classifier)
- Impact and Urgency assessment (rule-based cue word scoring)
- Strict deterministic Priority calculation matrix (P1 - P4)
- Deterministic security indicator overrides (account compromise, ransomware, malware)
- Missing information detection and clarification requirements
- Escalation determination

Uses in-house NLP engine only. No external LLM.
"""

import re
from typing import Optional, List, Dict, Any
from pathlib import Path
from pydantic import BaseModel, Field
from app.models.orm import TicketPriority
from app.services.nlp.classifier import NaiveBayesClassifier
from app.services.nlp.impact_urgency import score_impact_urgency
from app.services.nlp.slots import get_missing_slots
from app.config import settings
from app.utils.logger import logger


class TriageResult(BaseModel):
    category: str = Field(description="High-level category: network, account, security, hardware, software, email, performance, general")
    subcategory: Optional[str] = Field(default=None, description="Sub-category (e.g. wi-fi, vpn, credentials, phishing)")
    issue_summary: str = Field(description="Concise description of the user's issue")
    impact: str = Field(default="Medium", description="Business/User impact: High, Medium, Low")
    urgency: str = Field(default="Medium", description="Time sensitivity: High, Medium, Low")
    priority: TicketPriority = Field(default=TicketPriority.P3, description="Calculated priority: P1 (Critical), P2 (High), P3 (Medium), P4 (Low)")
    suggested_group: str = Field(default="End User Support", description="Assignment group: Security Operations, Network Infrastructure, IAM, End User Support, etc.")
    confidence: float = Field(default=0.85, description="Confidence score [0.0 - 1.0]")
    missing_information: List[str] = Field(default_factory=list, description="List of missing details needed to resolve or file")
    clarification_needed: bool = Field(default=False, description="Whether the user needs to provide more info before resolution")
    escalation_required: bool = Field(default=False, description="Whether immediate human/Tier-2 escalation is required")
    escalation_reason: Optional[str] = Field(default=None, description="Reason for escalation if required")


# Deterministic critical security indicators
# These are matched with word-boundary regex BEFORE the keyword fallback, ensuring
# genuine incidents (ransomware, phishing, credential compromise) always escalate to P1.
SECURITY_CRITICAL_KEYWORDS = [
    "compromised", "hacked", "ransomware", "malware", "phishing",
    "data leak", "data breach", "unauthorized access", "suspicious email",
    "wire transfer", "keylogger", "trojan", "bitcoin ransom",
    "account compromised", "credentials stolen", "identity theft",
]

# Deterministic IT category keyword mappings (keeps Phase 1 tests 100% compliant)
#
# IMPORTANT SAFETY RULE for the "security" bucket:
#   - Do NOT include the bare word "security" here. Sentences like
#     "Is there a security issue with my Wi-Fi?" would otherwise match,
#     triggering a false P1 escalation to SecOps.
#   - Do NOT include "compromised", "hacked", or "phishing" here;
#     those are caught by SECURITY_CRITICAL_KEYWORDS above, which fires first.
#   - Only include MFA/authenticator keywords, which represent an IAM
#     access problem (P2, no escalation), not a critical security incident.
CATEGORY_KEYWORDS = {
    "network": ["wi-fi", "wifi", "wireless", "internet", "network", "router", "vpn", "connectivity", "ethernet"],
    "account": ["password", "reset", "forgot", "credentials", "locked", "account locked", "unable to login", "login failed"],
    "security": ["mfa", "two-factor", "2fa", "authenticator", "otp", "one-time password"],
    "hardware": ["printer", "print", "printing", "monitor", "keyboard", "mouse", "laptop screen", "battery"],
    "software": ["install", "software", "application", "app", "program", "license"],
    "performance": ["slow", "performance", "lagging", "freezing", "hanging", "high cpu"],
    "email": ["email", "mail", "outlook", "sync", "inbox", "mailbox"],
}

ASSIGNMENT_GROUPS = {
    "security": "Security Operations",
    "network": "Network Infrastructure",
    "account": "Identity & Access Management",
    "hardware": "Hardware & Field Support",
    "software": "Application Support",
    "email": "Collaboration & Email Systems",
    "performance": "End User Support",
    "general": "End User Support",
}


def calculate_priority(impact: str, urgency: str) -> TicketPriority:
    """
    Standard ITIL Priority Matrix:
    - High Impact + High Urgency    -> P1 (Critical)
    - High Impact + Medium Urgency  -> P2 (High)
    - Medium Impact + High Urgency  -> P2 (High)
    - High Impact + Low Urgency     -> P3 (Medium)
    - Medium Impact + Medium Urgency-> P3 (Medium)
    - Low Impact + High Urgency     -> P3 (Medium)
    - Medium Impact + Low Urgency   -> P4 (Low)
    - Low Impact + Medium Urgency   -> P4 (Low)
    - Low Impact + Low Urgency      -> P4 (Low)
    """
    imp = impact.capitalize().strip()
    urg = urgency.capitalize().strip()

    if imp == "High" and urg == "High":
        return TicketPriority.P1
    elif (imp == "High" and urg == "Medium") or (imp == "Medium" and urg == "High"):
        return TicketPriority.P2
    elif (imp == "High" and urg == "Low") or (imp == "Medium" and urg == "Medium") or (imp == "Low" and urg == "High"):
        return TicketPriority.P3
    else:
        return TicketPriority.P4


class TicketTriageService:
    """Triage service using in-house Naive Bayes classifier with deterministic rules."""

    def __init__(self):
        self.classifier = self._load_classifier()

    def _load_classifier(self) -> NaiveBayesClassifier:
        """Load the trained Naive Bayes classifier."""
        model_path = settings.KNOWLEDGE_BASE_DIR.parent / "models" / "classifier.json"
        if model_path.exists():
            try:
                return NaiveBayesClassifier.load(model_path)
            except Exception as e:
                logger.warning(f"Failed to load classifier: {e}, using fallback triage")
                return None
        return None

    def triage_message(self, message: str, context: Optional[str] = None) -> TriageResult:
        """
        Analyze a support message and return a validated TriageResult.
        
        Enforces:
        1. Deterministic security critical keywords first (highest priority)
        2. Naive Bayes classification (if classifier loaded)
        3. Fallback keyword-based categorization
        4. Rule-based impact/urgency scoring
        5. ITIL priority matrix
        """
        lower = message.lower()

        # Rule 1: Check critical security indicators first (Deterministic Security Rule)
        is_security_incident = any(re.search(r"\b" + re.escape(kw) + r"\b", lower) for kw in SECURITY_CRITICAL_KEYWORDS)
        if is_security_incident:
            logger.warning(f"Security incident detected in message: '{message[:50]}...'")
            return TriageResult(
                category="security",
                subcategory="incident_response",
                issue_summary=message[:150],
                impact="High",
                urgency="High",
                priority=TicketPriority.P1,
                suggested_group="Security Operations",
                confidence=0.99,
                missing_information=[],
                clarification_needed=False,
                escalation_required=True,
                escalation_reason="Suspected security incident / compromise detected via deterministic security rules",
            )

        # Rule 2: Try Naive Bayes classification if available
        detected_category = "unknown"
        confidence = 0.0
        
        if self.classifier is not None:
            try:
                category, probs = self.classifier.predict(message)
                detected_category = category
                confidence = max(probs.values())
                
                # If confidence below threshold, escalate for clarification
                if confidence < getattr(settings, 'CLASSIFIER_CONFIDENCE_THRESHOLD', 0.5):
                    logger.info(f"Low classifier confidence ({confidence:.2f}) for category {category}")
                    detected_category = "unknown"
                    confidence = 0.0
            except Exception as e:
                logger.warning(f"Classifier prediction failed: {e}, using fallback")

        # Rule 3: Deterministic keyword-based fallback
        if detected_category == "unknown":
            for cat, keywords in CATEGORY_KEYWORDS.items():
                if any(re.search(r"\b" + re.escape(kw) + r"\b", lower) for kw in keywords):
                    detected_category = cat
                    confidence = 0.75
                    break

        # Fallback to context keywords if message alone is uncategorized
        if detected_category == "unknown" and context:
            lower_context = context.lower()
            for cat, keywords in CATEGORY_KEYWORDS.items():
                if any(re.search(r"\b" + re.escape(kw) + r"\b", lower_context) for kw in keywords):
                    detected_category = cat
                    confidence = 0.65
                    break

        # Rule-based impact and urgency scoring
        impact, urgency = score_impact_urgency(message)
        
        # Override with category-specific defaults if needed
        if detected_category == "security":
            impact = "Medium"
            urgency = "High"
        elif detected_category in ("account", "network"):
            if impact == "Low":
                impact = "Medium"
            if urgency == "Low":
                urgency = "High"

        # ITIL priority matrix
        priority = calculate_priority(impact, urgency)
        suggested_group = ASSIGNMENT_GROUPS.get(detected_category, "End User Support")

        # Escalation rules
        escalate = (detected_category == "unknown" or priority == TicketPriority.P1)
        clarify = len(message.split()) < 3 and detected_category == "unknown"
        
        # Slot-based clarification
        missing_slots = get_missing_slots(message, detected_category) if detected_category != "unknown" else []

        escalation_reason = None
        if priority == TicketPriority.P1:
            escalation_reason = "Critical P1 incident requires immediate escalation"
        elif detected_category == "unknown":
            escalation_reason = "Uncategorized or ambiguous issue requiring human technician review"

        return TriageResult(
            category=detected_category,
            subcategory=None,
            issue_summary=message[:150],
            impact=impact,
            urgency=urgency,
            priority=priority,
            suggested_group=suggested_group,
            confidence=confidence,
            missing_information=missing_slots,
            clarification_needed=clarify or (len(missing_slots) > 0),
            escalation_required=escalate,
            escalation_reason=escalation_reason,
        )
