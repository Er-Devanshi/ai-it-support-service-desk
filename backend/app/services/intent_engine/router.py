"""
Intent Router for ServiceDesk-AI.

Decides whether a message should be:
  (a) handled directly by an intent handler (greeting, thanks, goodbye,
      check_ticket_status, create_ticket), or
  (b) passed unchanged to the existing troubleshooting pipeline
      (triage → retrieval → escalation rules → extractive responder).

Ordering contract (unchanged from existing pipeline):
  Security critical-keyword detection  ← lives in triage_node, runs FIRST
  Intent router                        ← this module, runs AFTER triage
  BM25 retrieval / escalation / answer ← existing pipeline, runs LAST

Guard rules (amendment 4):
  greeting / thanks / goodbye are only handled directly when ALL of:
    1. message token count <= INTENT_SHORT_MSG_TOKENS (default 6)
    2. message contains no technical keyword from TECHNICAL_KEYWORDS set

  Any message that contains a technical keyword goes to the pipeline,
  even when the classifier predicts greeting/thanks/goodbye.
  Examples that must NOT be caught by small-talk handlers:
    "hi, my VPN is down"            → troubleshoot (has 'vpn')
    "thanks but wifi still broken"  → troubleshoot (has 'wifi')
    "good morning, printer offline" → troubleshoot (has 'printer')
"""

import re
from typing import Dict, Any, Tuple

from app.config import settings
from app.services.intent_engine.intent_classifier import classify
from app.utils.logger import logger


# ---------------------------------------------------------------------------
# Technical keyword guard
# ---------------------------------------------------------------------------
# Any message that contains one of these words must go to the pipeline,
# regardless of the intent classifier output.
# This list covers the domains of the knowledge base files.
TECHNICAL_KEYWORDS = {
    # Network / VPN / Wi-Fi
    "wifi", "wi-fi", "wireless", "vpn", "internet", "network", "ethernet",
    "router", "connectivity", "bandwidth", "hotspot", "proxy", "firewall",
    "dns", "dhcp", "ip", "ping", "latency",
    # Account / identity
    "password", "login", "logout", "credential", "mfa", "2fa", "otp",
    "authenticator", "ldap", "sso", "active directory", "account",
    "locked", "unlock", "reset", "expire",
    # Email / collaboration
    "email", "outlook", "mailbox", "inbox", "sync", "calendar", "teams",
    "sharepoint", "onedrive",
    # Hardware / peripherals
    "laptop", "desktop", "monitor", "screen", "printer", "keyboard",
    "mouse", "usb", "battery", "power", "charger", "headset",
    # Software / OS
    "install", "software", "application", "app", "update", "upgrade",
    "license", "crash", "error", "blue screen", "bsod", "windows",
    "macos", "linux",
    # Performance
    "slow", "freeze", "hang", "cpu", "ram", "memory", "disk", "storage",
    # Network drives / files
    "drive", "share", "folder", "smb", "mapped drive", "file server",
    # Security incidents (belt-and-suspenders; triage already handles these)
    "ransomware", "malware", "phishing", "hacked", "compromised",
}

# Intents that require the short-message guard before being handled directly
_SMALL_TALK_INTENTS = {"greeting", "thanks", "goodbye"}


def _has_technical_keyword(message: str) -> bool:
    """Return True if any technical keyword appears in the message."""
    lower = message.lower()
    for kw in TECHNICAL_KEYWORDS:
        # Use word boundary check for single-word keywords
        if " " in kw:
            if kw in lower:
                return True
        else:
            if re.search(r"\b" + re.escape(kw) + r"\b", lower):
                return True
    return False


def _token_count(message: str) -> int:
    """Rough whitespace-split token count."""
    return len(message.split())


# ---------------------------------------------------------------------------
# Public routing function
# ---------------------------------------------------------------------------

def route_intent(message: str, state: Dict[str, Any]) -> Tuple[str, float, str]:
    """
    Classify the message intent and decide the routing target.

    Returns:
        (intent, confidence, routing_target)
        routing_target is one of:
          "greeting" | "thanks" | "goodbye"
          "check_ticket_status"
          "create_ticket"
          "pipeline"   ← pass to existing BM25/escalation pipeline

    Rules:
      1. If USE_INTENT flag is False → always return ("troubleshoot", 1.0, "pipeline")
      2. Classify with intent classifier.
      3. If intent is a small-talk intent (greeting/thanks/goodbye):
           - Only handle directly if token count <= INTENT_SHORT_MSG_TOKENS
             AND no technical keyword present.
           - Otherwise route to pipeline.
      4. If intent is check_ticket_status or create_ticket → handle directly.
      5. If intent is troubleshoot OR confidence < INTENT_CONFIDENCE_THRESHOLD
         → route to pipeline.
    """
    # Feature flag: when off, behave identically to the original pipeline
    if not getattr(settings, "USE_INTENT", False):
        return ("troubleshoot", 1.0, "pipeline")

    intent, confidence = classify(message)

    logger.debug(
        f"[IntentRouter] intent={intent!r} confidence={confidence:.3f} "
        f"msg={message[:60]!r}"
    )

    # --- small-talk guard (amendment 4) ---
    if intent in _SMALL_TALK_INTENTS:
        token_limit = getattr(settings, "INTENT_SHORT_MSG_TOKENS", 6)
        if _token_count(message) > token_limit or _has_technical_keyword(message):
            # Message is complex or technical — send to pipeline
            logger.debug(
                f"[IntentRouter] Small-talk guard fired for intent={intent!r}; "
                "routing to pipeline."
            )
            return (intent, confidence, "pipeline")
        # Short, non-technical small talk → handle directly
        return (intent, confidence, intent)

    # --- explicit ticket intents ---
    if intent in ("check_ticket_status", "create_ticket"):
        # Still route to pipeline if confidence is too low
        threshold = getattr(settings, "INTENT_CONFIDENCE_THRESHOLD", 0.6)
        if confidence < threshold:
            logger.debug(
                f"[IntentRouter] Low confidence ({confidence:.3f}) for {intent!r}; "
                "routing to pipeline."
            )
            return (intent, confidence, "pipeline")
        return (intent, confidence, intent)

    # --- troubleshoot or low-confidence fallback ---
    return (intent, confidence, "pipeline")
