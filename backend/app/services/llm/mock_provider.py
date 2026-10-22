"""
Mock LLM Provider for offline demonstration, unit testing, and fallback.
Explicitly identifies simulated responses to avoid misleading users or faculty mentors.
"""

from typing import Optional, Type, TypeVar
import json
import re
from pydantic import BaseModel
from app.services.llm.base import BaseLLMProvider, LLMResponse

T = TypeVar("T", bound=BaseModel)


class MockLLMProvider(BaseLLMProvider):
    """
    Mock / Demo LLM provider that simulates intelligent responses
    without connecting to external paid or quota-limited APIs.
    """

    def __init__(self, model_name: str = "mock-servicedesk-ai"):
        super().__init__(model_name=model_name)

    def generate(
        self,
        prompt: str,
        system_instruction: str = "",
        max_tokens: int = 1024,
        temperature: float = 0.2,
    ) -> LLMResponse:
        """Simulate an LLM response tailored to the prompt content."""
        lower = prompt.lower()

        # Check if structured output is requested by checking system instruction
        if "JSON Schema" in system_instruction:
            simulated_json = self._simulate_structured_json(prompt=lower)
            return LLMResponse(
                content=simulated_json,
                model=self.model_name,
                provider="mock",
                is_mock=True,
                usage={"prompt_tokens": 50, "completion_tokens": 100, "total_tokens": 150},
            )

        # Natural language response simulation
        if "wifi" in lower or "wi-fi" in lower or "internet" in lower or "network" in lower:
            text = (
                "[Demo/Mock Mode] Here are the recommended troubleshooting steps for your Wi-Fi and network issue:\n"
                "1. Verify your network adapter is enabled in system settings.\n"
                "2. Disconnect and reconnect to the enterprise SSID (e.g. 'Corp-Secure').\n"
                "3. Flush your local DNS cache (`ipconfig /flushdns`).\n"
                "4. If multiple colleagues in your area are experiencing the same issue, this may indicate a switch or DHCP outage.\n\n"
                "Would you like me to open a network support ticket for you?"
            )
        elif "password" in lower or "reset" in lower:
            text = (
                "[Demo/Mock Mode] For password resets:\n"
                "1. Navigate to the employee identity self-service portal.\n"
                "2. Click 'Reset Password' and verify via secondary MFA authenticator.\n"
                "3. Ensure the new password meets our 12-character complexity requirements.\n\n"
                "If you are locked out from self-service, I can request an account unlock workflow."
            )
        elif "compromise" in lower or "hacked" in lower or "phishing" in lower or "malware" in lower:
            text = (
                "[Demo/Mock Mode] 🚨 SECURITY INCIDENT DETECTED.\n"
                "Your request has been flagged for immediate escalation to Security Operations (SecOps).\n"
                "Please disconnect your device from the corporate network immediately and do not enter any further credentials."
            )
        elif "slow" in lower or "performance" in lower:
            text = (
                "[Demo/Mock Mode] For system performance issues:\n"
                "1. Check Task Manager / Activity Monitor for runaway processes consuming CPU or Memory.\n"
                "2. Ensure you have at least 15% free disk space.\n"
                "3. Reboot the workstation to clear unreleased file handles."
            )
        else:
            text = (
                f"[Demo/Mock Mode] I have analyzed your request regarding: '{prompt[:60]}...'.\n"
                "Based on the enterprise IT guidelines, please verify your credentials and network connection. "
                "If this does not resolve the issue, a ticket can be automatically created for technician review."
            )

        return LLMResponse(
            content=text,
            model=self.model_name,
            provider="mock",
            is_mock=True,
            usage={"prompt_tokens": 40, "completion_tokens": 80, "total_tokens": 120},
        )

    def _simulate_structured_json(self, prompt: str) -> str:
        """
        Produce schema-compatible JSON for triage based on user prompt.
        All keyword checks use whole-word regex (\\b boundaries) to prevent
        false positives like 'app' matching inside 'happened'.
        """

        def _has(keywords: list) -> bool:
            return any(re.search(r"\b" + re.escape(kw) + r"\b", prompt) for kw in keywords)

        # 1. Critical security incident check
        # Uses word-boundary matching for most terms; stem matching only for distinctive
        # multi-character stems that cannot appear in innocent IT vocabulary.
        _security_stems = ("ransomware", "malware", "keylogger", "trojan", "phishing")
        _security_exact = ("hacked", "compromised", "data breach", "data leak",
                           "unauthorized access", "suspicious email", "wire transfer",
                           "bitcoin ransom", "credentials stolen", "identity theft")
        is_security_incident = (
            any(re.search(r"\b" + re.escape(kw) + r"\b", prompt) for kw in _security_exact)
            or any(kw in prompt for kw in _security_stems)
        )
        if is_security_incident:
            return json.dumps({
                "category": "security",
                "subcategory": "incident_response",
                "issue_summary": "Suspected security incident reported by user",
                "impact": "High",
                "urgency": "High",
                "priority": "P1",
                "suggested_group": "Security Operations",
                "confidence": 0.98,
                "missing_information": [],
                "clarification_needed": False,
                "escalation_required": True,
                "escalation_reason": "Suspected security incident or compromise"
            })

        # 2. Network / Wi-Fi (whole-word)
        elif _has(["wi-fi", "wifi", "wireless", "internet", "network", "vpn", "connectivity", "ethernet"]):
            return json.dumps({
                "category": "network",
                "subcategory": "connectivity",
                "issue_summary": "Network or Wi-Fi connectivity issue",
                "impact": "Medium",
                "urgency": "Medium",
                "priority": "P3",
                "suggested_group": "Network Infrastructure",
                "confidence": 0.92,
                "missing_information": [],
                "clarification_needed": False,
                "escalation_required": False,
                "escalation_reason": None
            })

        # 3. Account / Password / Lock (whole-word)
        elif _has(["password", "reset", "forgot", "credentials", "locked", "login"]):
            return json.dumps({
                "category": "account",
                "subcategory": "credentials",
                "issue_summary": "User account login or password issue",
                "impact": "Medium",
                "urgency": "High",
                "priority": "P2",
                "suggested_group": "Identity & Access Management",
                "confidence": 0.95,
                "missing_information": [],
                "clarification_needed": False,
                "escalation_required": False,
                "escalation_reason": None
            })

        # 4. MFA / 2FA (whole-word) — IAM access issue, not a critical incident
        elif _has(["mfa", "2fa", "two-factor", "authenticator", "otp"]):
            return json.dumps({
                "category": "security",
                "subcategory": "mfa",
                "issue_summary": "MFA or Authenticator token issue",
                "impact": "Medium",
                "urgency": "High",
                "priority": "P2",
                "suggested_group": "Identity & Access Management",
                "confidence": 0.92,
                "missing_information": [],
                "clarification_needed": False,
                "escalation_required": False,
                "escalation_reason": None
            })

        # 5. Hardware / Printer (whole-word)
        elif _has(["printer", "print", "printing", "monitor", "hardware"]):
            return json.dumps({
                "category": "hardware",
                "subcategory": "printing",
                "issue_summary": "Hardware or printer malfunction",
                "impact": "Low",
                "urgency": "Medium",
                "priority": "P3",
                "suggested_group": "Hardware & Field Support",
                "confidence": 0.90,
                "missing_information": [],
                "clarification_needed": False,
                "escalation_required": False,
                "escalation_reason": None
            })

        # 6. Software installation (whole-word — prevents "app" matching "happened")
        elif _has(["install", "software", "application", "app", "program"]):
            return json.dumps({
                "category": "software",
                "subcategory": "installation",
                "issue_summary": "Software installation request",
                "impact": "Low",
                "urgency": "Low",
                "priority": "P4",
                "suggested_group": "Application Support",
                "confidence": 0.90,
                "missing_information": [],
                "clarification_needed": False,
                "escalation_required": False,
                "escalation_reason": None
            })

        # 7. Performance (whole-word)
        elif _has(["slow", "performance", "lagging", "freezing", "hanging"]):
            return json.dumps({
                "category": "performance",
                "subcategory": "workstation",
                "issue_summary": "System sluggishness or high resource usage",
                "impact": "Low",
                "urgency": "Medium",
                "priority": "P3",
                "suggested_group": "End User Support",
                "confidence": 0.88,
                "missing_information": [],
                "clarification_needed": False,
                "escalation_required": False,
                "escalation_reason": None
            })

        # 8. Email sync (whole-word — prevents "mail" matching "email" substring issues)
        elif _has(["email", "mail", "outlook", "sync", "inbox"]):
            return json.dumps({
                "category": "email",
                "subcategory": "sync",
                "issue_summary": "Email synchronization issue",
                "impact": "Medium",
                "urgency": "Medium",
                "priority": "P3",
                "suggested_group": "Collaboration & Email Systems",
                "confidence": 0.92,
                "missing_information": [],
                "clarification_needed": False,
                "escalation_required": False,
                "escalation_reason": None
            })

        # 9. Unusual / Unrecognized -> Escalate (whole-word)
        elif _has(["unusual", "strange", "unknown", "bizarre"]):
            return json.dumps({
                "category": "unknown",
                "subcategory": "unclassified",
                "issue_summary": "Unrecognized issue requiring technician review",
                "impact": "Low",
                "urgency": "Low",
                "priority": "P4",
                "suggested_group": "End User Support",
                "confidence": 0.30,
                "missing_information": ["Detailed error message"],
                "clarification_needed": True,
                "escalation_required": True,
                "escalation_reason": "Unrecognized issue pattern"
            })

        # 10. General fallback — no keywords matched
        return json.dumps({
            "category": "general",
            "subcategory": "inquiry",
            "issue_summary": "General IT inquiry",
            "impact": "Low",
            "urgency": "Low",
            "priority": "P4",
            "suggested_group": "End User Support",
            "confidence": 0.70,
            "missing_information": [],
            "clarification_needed": False,
            "escalation_required": False,
            "escalation_reason": None
        })
