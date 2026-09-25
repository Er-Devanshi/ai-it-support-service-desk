"""
Chat service — Phase 1 placeholder implementation.

This module contains the core logic that processes a user message and produces
a response. In Phase 1 there is NO LLM or RAG involved. The function uses
simple keyword matching against common IT issues to return a useful-looking
response so the full request/response pipeline can be tested end-to-end.

Phase 2 will replace `process_message()` with an actual LLM call and
RAG retrieval over the knowledge base.
"""

import re

from app.models.chat import ChatResponse

# ---------------------------------------------------------------------------
# Keyword → (category, reply) mapping
# Each entry covers a common IT support topic from the knowledge base.
# Keep this list in sync with data/knowledge_base/sample_it_faq.txt.
# ---------------------------------------------------------------------------

def _word_in(word: str, text: str) -> bool:
    """
    Return True if `word` appears as a whole word inside `text`.
    Using word boundaries avoids false positives like 'app' matching 'happened'.
    """
    return bool(re.search(r"\b" + re.escape(word) + r"\b", text))


KEYWORD_RULES: list[tuple[list[str], str, str]] = [
    (
        ["wi-fi", "wifi", "wireless", "internet", "network"],
        "network",
        (
            "Try the following steps for Wi-Fi issues:\n"
            "1. Restart your device and the Wi-Fi router.\n"
            "2. Forget the network and reconnect.\n"
            "3. Make sure Airplane Mode is off.\n"
            "4. Check if other devices can connect — if not, the issue may be with the router.\n"
            "If the problem persists, please raise a support ticket."
        ),
    ),
    (
        ["password", "reset", "forgot", "credentials"],
        "account",
        (
            "To reset your password:\n"
            "1. Visit the company self-service portal and click 'Forgot Password'.\n"
            "2. Enter your registered work email address.\n"
            "3. Follow the link sent to your email.\n"
            "If you cannot access your email, contact IT support directly."
        ),
    ),
    (
        ["vpn", "remote", "connect from home"],
        "network",
        (
            "For VPN connection issues:\n"
            "1. Ensure you are connected to the internet first.\n"
            "2. Open the VPN client and try reconnecting.\n"
            "3. Verify your credentials are correct.\n"
            "4. Check if your VPN subscription/license is active.\n"
            "Contact IT if the issue continues."
        ),
    ),
    (
        ["email", "mail", "outlook", "sync", "inbox"],
        "email",
        (
            "For email not syncing:\n"
            "1. Check your internet connection.\n"
            "2. Restart your email client (Outlook/Thunderbird).\n"
            "3. Remove and re-add your email account.\n"
            "4. Ensure your mailbox is not full (check storage quota).\n"
            "Reach out to IT if the problem continues."
        ),
    ),
    (
        ["printer", "print", "printing"],
        "hardware",
        (
            "For printer issues:\n"
            "1. Confirm the printer is powered on and connected to the network.\n"
            "2. Remove any stuck print jobs from the print queue.\n"
            "3. Restart the print spooler service (Windows: services.msc → Print Spooler).\n"
            "4. Reinstall the printer driver if needed.\n"
            "IT can assist if the printer is shared or network-managed."
        ),
    ),
    (
        ["install", "software", "application", "app", "program"],
        "software",
        (
            "For software installation requests:\n"
            "1. Check if the software is available in the company's self-service portal.\n"
            "2. If not listed, submit a software request ticket with the business justification.\n"
            "3. Do not install unlicensed or personal software on work devices.\n"
            "Approvals may be required depending on the software category."
        ),
    ),
    (
        ["locked", "account locked", "unable to login", "login failed"],
        "account",
        (
            "If your account is locked:\n"
            "1. Wait 15 minutes and try again — accounts auto-unlock after repeated failures.\n"
            "2. Use the self-service unlock tool on the IT portal.\n"
            "3. Contact the IT helpdesk if you need immediate access.\n"
            "Repeated lockouts may indicate a compromised credential — please report this."
        ),
    ),
    (
        ["slow", "performance", "lagging", "freezing", "hanging"],
        "performance",
        (
            "For a slow or unresponsive computer:\n"
            "1. Restart your machine — this clears temporary files and running processes.\n"
            "2. Check available disk space (keep at least 10% free).\n"
            "3. Close unused applications and browser tabs.\n"
            "4. Run a malware scan.\n"
            "5. If issues persist, IT may need to inspect the hardware or re-image the device."
        ),
    ),
    (
        ["mfa", "two-factor", "2fa", "authenticator", "otp", "one-time"],
        "security",
        (
            "For MFA / two-factor authentication issues:\n"
            "1. Ensure the time on your authenticator device is correct (MFA is time-sensitive).\n"
            "2. Try generating a new code and entering it quickly.\n"
            "3. If you lost access to your authenticator app, contact IT to reset your MFA device.\n"
            "Never share your OTP with anyone, including IT staff."
        ),
    ),
    (
        ["network", "connectivity", "no internet", "disconnected", "ethernet"],
        "network",
        (
            "For general network connectivity issues:\n"
            "1. Check if your ethernet cable is securely plugged in.\n"
            "2. Restart your network adapter (disable and re-enable in device settings).\n"
            "3. Flush DNS: open Command Prompt and run `ipconfig /flushdns`.\n"
            "4. Try pinging 8.8.8.8 to test basic connectivity.\n"
            "Escalate to IT if the entire team is affected — it may be a network outage."
        ),
    ),
]

# Fallback when no keyword matches
_FALLBACK_REPLY = (
    "Thank you for contacting ServiceDesk-AI. I was not able to automatically "
    "categorise your issue in this early version.\n\n"
    "Please describe your problem in more detail, or contact the IT helpdesk "
    "directly so a technician can assist you."
)


# ---------------------------------------------------------------------------
# Public function
# ---------------------------------------------------------------------------

def process_message(message: str) -> ChatResponse:
    """
    Match the user message against known IT issue keywords and return
    a structured ChatResponse.

    This is a Phase 1 stub. Replace with an LLM call in Phase 2.
    """
    lower = message.lower()

    for keywords, category, reply in KEYWORD_RULES:
        if any(_word_in(kw, lower) for kw in keywords):
            return ChatResponse(
                reply=reply,
                category=category,
                status="answered",
                note="Phase 1 — rule-based response. LLM/RAG not yet connected.",
            )

    # Nothing matched
    return ChatResponse(
        reply=_FALLBACK_REPLY,
        category="unknown",
        status="escalate",
        note="Phase 1 — no keyword match found. Will be handled by LLM in Phase 2.",
    )
