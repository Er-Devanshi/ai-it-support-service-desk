"""
Dedicated AI Ticket Triage and Prioritization Service for ServiceDesk-AI.

Implements:
- Category & subcategory classification
- Impact and Urgency assessment
- Strict deterministic Priority calculation matrix (P1 - P4)
- Deterministic security indicator overrides (account compromise, ransomware, malware)
- Missing information detection and clarification requirements
- Escalation determination
"""

import re
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from app.models.orm import TicketPriority
from app.services.llm.base import BaseLLMProvider
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
SECURITY_CRITICAL_KEYWORDS = [
    "compromised", "hacked", "ransomware", "malware", "phishing",
    "data leak", "data breach", "unauthorized access", "suspicious email",
    "wire transfer", "keylogger", "trojan", "bitcoin ransom"
]

# Deterministic IT category keyword mappings (keeps Phase 1 tests 100% compliant)
CATEGORY_KEYWORDS = {
    "network": ["wi-fi", "wifi", "wireless", "internet", "network", "router", "vpn", "connectivity", "ethernet"],
    "account": ["password", "reset", "forgot", "credentials", "locked", "account locked", "unable to login", "login failed"],
    "security": ["mfa", "two-factor", "2fa", "authenticator", "otp", "one-time", "security", "compromised", "hacked", "phishing"],
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
    """Triage service combining deterministic rules with LLM intelligence."""

    def __init__(self, llm_provider: Optional[BaseLLMProvider] = None):
        self.llm_provider = llm_provider

    def triage_message(self, message: str) -> TriageResult:
        """
        Analyze a support message and return a validated TriageResult.
        Enforces deterministic rules on security and critical indicators.
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

        # Rule 2: Try LLM-based triage if an LLM provider is available
        if self.llm_provider is not None:
            try:
                system_prompt = (
                    "You are an expert IT Service Desk Triage Agent. "
                    "Analyze the user's issue and classify it into category, subcategory, impact (High, Medium, Low), "
                    "urgency (High, Medium, Low), suggested assignment group, confidence (0.0 to 1.0), "
                    "missing_information (list), clarification_needed (bool), and escalation_required (bool)."
                )
                user_prompt = f"IT Support Message:\n\"\"\"{message}\"\"\""
                
                llm_triage = self.llm_provider.generate_structured(
                    prompt=user_prompt,
                    schema=TriageResult,
                    system_instruction=system_prompt,
                )
                # Recalculate priority deterministically using impact and urgency
                llm_triage.priority = calculate_priority(llm_triage.impact, llm_triage.urgency)
                return llm_triage
            except Exception as e:
                logger.warning(f"LLM triage failed, falling back to deterministic triage: {e}")

        # Rule 3: Deterministic keyword-based triage fallback
        detected_category = "unknown"
        for cat, keywords in CATEGORY_KEYWORDS.items():
            if any(re.search(r"\b" + re.escape(kw) + r"\b", lower) for kw in keywords):
                detected_category = cat
                break

        impact = "Medium"
        urgency = "Medium"
        if detected_category == "security":
            impact = "High"
            urgency = "High"
        elif detected_category in ("account", "network"):
            impact = "Medium"
            urgency = "High"
        elif detected_category == "unknown":
            impact = "Low"
            urgency = "Low"

        priority = calculate_priority(impact, urgency)
        suggested_group = ASSIGNMENT_GROUPS.get(detected_category, "End User Support")

        escalate = (detected_category == "unknown")
        clarify = len(message.split()) < 3 and detected_category == "unknown"

        return TriageResult(
            category=detected_category,
            subcategory=None,
            issue_summary=message[:150],
            impact=impact,
            urgency=urgency,
            priority=priority,
            suggested_group=suggested_group,
            confidence=0.80 if detected_category != "unknown" else 0.40,
            missing_information=["More specific description"] if clarify else [],
            clarification_needed=clarify,
            escalation_required=escalate,
            escalation_reason="Uncategorized or ambiguous issue requiring human technician review" if escalate else None,
        )
