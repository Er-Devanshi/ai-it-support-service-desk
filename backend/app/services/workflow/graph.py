"""
LangGraph Multi-Agent Workflow Implementation for ServiceDesk-AI.

Explicit StateGraph with:
- Intake & Context Node
- Triage & Intent Detection Node
- Security Check & Escalation Node
- RAG Knowledge Retrieval Node
- Action Decision & Authorization Node
- Action Execution & Approval Trigger Node
- Response Generation Node
- Outcome Verification Node
- Conditional Routing and Bounded Termination
"""

from typing import Dict, Any, Optional
import uuid
import re

from langgraph.graph import StateGraph, START, END

from app.services.workflow.state import ServiceDeskState
from app.services.triage_service import TicketTriageService, TriageResult
from app.services.rag.retrieval_interface import get_retriever
from app.services.actions.action_registry import (
    get_action_definition,
    execute_action,
    ACTION_REGISTRY,
)
from app.services.approval_service import create_approval_request
from app.services.ticket_service import create_ticket
from app.services.conversation_service import (
    get_history,
    save_message,
    format_history_for_llm,
)
from app.models.ticket_schemas import TicketCreate
from app.services.llm.base import BaseLLMProvider
from app.services.llm.factory import get_llm_provider
from app.db.session import SessionLocal
from app.models.orm import User
from app.utils.logger import logger


# ---------------------------------------------------------------------------
# Phase 1 Preserved Keyword Matching for 100% Backward Compatibility
# ---------------------------------------------------------------------------
KEYWORD_RULES = [
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


def _detect_ticket_intent(message_lower: str) -> bool:
    """
    Return True when the user is explicitly asking to create/open/raise a ticket.
    Uses a flexible pattern: any creation verb near the word "ticket".
    This catches phrasings like:
      - "create a ticket"
      - "open a support ticket"
      - "raise a ticket"
      - "please create a support ticket"
      - "submit a new ticket"
      - "log a ticket for me"
      - "file a support request"
    """
    # Fast exact-phrase check first (most common forms)
    exact_phrases = [
        "create ticket", "open ticket", "raise ticket", "log ticket",
        "submit ticket", "file ticket",
        "create a ticket", "open a ticket", "raise a ticket",
        "create a support ticket", "open a support ticket",
        "raise a support ticket", "submit a support ticket",
        "log a support ticket", "file a support ticket",
        "create new ticket", "open new ticket",
        "create support ticket", "open support ticket",
    ]
    if any(phrase in message_lower for phrase in exact_phrases):
        return True

    # Flexible regex: creation-verb + optional words + "ticket"
    creation_verb_pattern = re.compile(
        r"\b(create|open|raise|log|submit|file|start|make|generate|initiate)\b"
        r".{0,25}"
        r"\bticket\b",
        re.IGNORECASE,
    )
    return bool(creation_verb_pattern.search(message_lower))


def match_phase1_rule(message: str) -> Optional[tuple[str, str]]:
    """Return (category, reply) if exact keyword rule matched."""
    lower = message.lower()
    for keywords, category, reply in KEYWORD_RULES:
        if any(bool(re.search(r"\b" + re.escape(kw) + r"\b", lower)) for kw in keywords):
            return category, reply
    return None


# ---------------------------------------------------------------------------
# Node Definitions
# ---------------------------------------------------------------------------

def intake_node(state: ServiceDeskState) -> Dict[str, Any]:
    """Intake node: initializes session identifiers, loads conversation history, and saves the user message."""
    logger.debug(f"[Workflow Intake] Processing conversation {state.get('conversation_id')}")
    iterations = state.get("iteration_count", 0) + 1

    # Persist the incoming user message for multi-turn memory
    db = SessionLocal()
    try:
        save_message(
            db=db,
            conversation_id=state["conversation_id"],
            role="user",
            content=state["message"],
            user_id=state.get("user_id"),
        )
        history_rows = get_history(db, state["conversation_id"])
        history_text = format_history_for_llm(history_rows[:-1])  # exclude the message just saved
    except Exception as e:
        logger.warning(f"[Intake] Conversation history operation failed: {e}")
        history_text = ""
    finally:
        db.close()

    return {
        "iteration_count": iterations,
        "is_terminal": iterations > 5,
        "conversation_history": history_text,
    }


def triage_node(state: ServiceDeskState) -> Dict[str, Any]:
    """Triage node: runs category classification, priority calculation, and security scan."""
    message = state.get("message", "")
    llm = get_llm_provider(allow_fallback=True)
    triage_service = TicketTriageService(llm_provider=llm)
    triage_result = triage_service.triage_message(message)

    is_sec = (triage_result.category == "security" and triage_result.escalation_required) or (
        "incident_response" in str(triage_result.subcategory)
    )

    return {
        "triage": triage_result.model_dump(),
        "is_security_incident": is_sec,
        "escalation_needed": triage_result.escalation_required,
        "escalation_reason": triage_result.escalation_reason,
    }


def security_escalation_node(state: ServiceDeskState) -> Dict[str, Any]:
    """Security escalation node: flags critical security threat and prescribes SecOps action."""
    message = state.get("message", "")
    triage = state.get("triage", {})
    reason = state.get("escalation_reason") or "Security incident detected"

    reply = (
        "🚨 **CRITICAL SECURITY ALERT**\n\n"
        f"Your request has been classified as a potential security incident ({reason}).\n"
        "**Actions Taken:**\n"
        "1. This incident has been escalated immediately to the **Security Operations Center (SecOps)**.\n"
        "2. A high-priority P1 security investigation ticket has been logged.\n\n"
        "**Immediate Safety Instructions:**\n"
        "• Immediately disconnect your workstation from Wi-Fi and Ethernet.\n"
        "• Do NOT enter any corporate credentials or passwords.\n"
        "• Keep this device powered on for forensic inspection by the Security team."
    )

    return {
        "final_reply": reply,
        "final_status": "escalate",
        "escalation_needed": True,
        "note": "Automated security rule triggered: Escalated to SecOps.",
    }


def rag_retrieval_node(state: ServiceDeskState) -> Dict[str, Any]:
    """RAG node: queries Sanskriti's retrieval interface."""
    message = state.get("message", "")
    retriever = get_retriever()
    res = retriever.retrieve(query=message, top_k=2)

    retrieved = []
    citations = []
    if res.is_available and res.documents:
        for doc in res.documents:
            retrieved.append(doc.model_dump())
            citations.append({
                "source": doc.source,
                "title": doc.title,
                "snippet": doc.content[:200] + "..." if len(doc.content) > 200 else doc.content,
                "relevance_score": doc.relevance_score,
            })

    return {
        "retrieved_docs": retrieved,
        "citations": citations,
    }


def action_decision_node(state: ServiceDeskState) -> Dict[str, Any]:
    """Action decision node: checks if the request triggers a permitted simulated IT action."""
    message = state.get("message", "").lower()
    action_req = None
    approval_needed = False

    # Detect action intent safely from allowlist
    if "unlock" in message and ("account" in message or "user" in message):
        action_req = {"action_name": "unlock_account", "params": {"username": "employee"}}
        approval_needed = True
    elif "reset" in message and "password" in message and ("force" in message or "temporary" in message):
        action_req = {"action_name": "reset_password", "params": {"username": "employee"}}
        approval_needed = True
    elif "check" in message and ("account" in message or "status" in message):
        action_req = {"action_name": "check_account_status", "params": {"username": "employee"}}
        approval_needed = False
    elif "is" in message and ("vpn" in message or "wifi" in message or "service" in message) and ("down" in message or "up" in message or "working" in message):
        svc_target = "vpn" if "vpn" in message else "wifi"
        action_req = {"action_name": "check_service_health", "params": {"service_name": svc_target}}
        approval_needed = False
    elif "grant" in message and "access" in message:
        action_req = {"action_name": "grant_resource_access", "params": {"username": "employee", "resource": "Restricted-DB"}}
        approval_needed = True

    return {
        "action_requested": action_req,
        "approval_needed": approval_needed,
    }


def action_execution_node(state: ServiceDeskState) -> Dict[str, Any]:
    """Action execution node: executes low-risk action or creates pending approval for high-risk action."""
    action_req = state.get("action_requested")
    if not action_req:
        return {}

    action_name = action_req["action_name"]
    params = action_req.get("params", {})
    action_def = get_action_definition(action_name)

    if not action_def:
        return {
            "action_result": {"success": False, "message": f"Action '{action_name}' is not in allowlist."},
        }

    # If action requires approval, generate ApprovalRequest
    if action_def.requires_approval:
        db = SessionLocal()
        try:
            user_id = state.get("user_id")
            user = db.query(User).filter(User.id == user_id).first() if user_id else None
            appr = create_approval_request(
                db=db,
                action_name=action_name,
                action_params=params,
                reason=f"User requested {action_name} through conversational IT assistant.",
                requester=user,
                conversation_id=state.get("conversation_id"),
                risk_level=action_def.risk_level,
            )
            return {
                "approval_needed": True,
                "approval_id": appr.id,
                "final_status": "pending_approval",
            }
        finally:
            db.close()

    # Otherwise, execute low-risk simulated action
    res = execute_action(action_name, params)
    return {
        "action_result": res.model_dump(),
    }


def response_generation_node(state: ServiceDeskState) -> Dict[str, Any]:
    """Response generation node: synthesizes troubleshooting reply, grounding with knowledge and action results."""
    message = state.get("message", "")
    triage = state.get("triage", {})
    action_result = state.get("action_result")
    approval_id = state.get("approval_id")
    approval_needed = state.get("approval_needed")
    docs = state.get("retrieved_docs", [])
    history_text = state.get("conversation_history", "")

    # If an approval was created, inform user clearly
    if approval_needed and approval_id:
        action_name = state.get("action_requested", {}).get("action_name", "action")
        reply = (
            f"⚠️ **Approval Required for Protected Action**\n\n"
            f"The requested action (`{action_name}`) requires human authorization before execution.\n"
            f"• **Approval Request ID:** `{approval_id}`\n"
            f"• **Status:** Pending decision by Support Agent or Administrator.\n\n"
            f"Once an authorized administrator approves this request, the simulated action will proceed automatically."
        )
        return {
            "final_reply": reply,
            "final_status": "pending_approval",
            "note": "Human-in-the-loop approval created.",
            "mode": "mock",
        }

    # If an action was executed directly
    if action_result:
        reply = (
            f"⚙️ **Simulated IT Action Executed:**\n\n"
            f"{action_result.get('message')}\n\n"
            f"*(Note: This is a safe simulation using synthetic enterprise records. No real company systems were altered.)*"
        )
        return {
            "final_reply": reply,
            "final_status": "answered",
            "note": "Controlled action simulation executed successfully.",
            "mode": "mock",
        }

    # Check Phase 1 exact canned match (guarantees backward compatibility with verify_phase1.py)
    # If the user also requested a ticket, we still serve the canned troubleshooting reply —
    # ticket_creation_node runs after this node and will persist the ticket.
    canned = match_phase1_rule(message)
    if canned:
        cat, reply = canned
        # If user also requested a ticket, append a note so they know it will be created
        if _detect_ticket_intent(message.lower()):
            reply = reply + "\n\n✅ A support ticket is being created for this issue."
        return {
            "final_reply": reply,
            "final_status": "answered",
            "note": "Matched standard IT knowledge base resolution.",
            "mode": "rule_fallback",
        }

    # If uncategorized or marked for escalation
    if triage.get("escalation_required") or triage.get("category") == "unknown":
        reply = (
            "Thank you for contacting ServiceDesk-AI. I was not able to automatically "
            "categorise your issue in this early version.\n\n"
            "Please describe your problem in more detail, or contact the IT helpdesk "
            "directly so a technician can assist you."
        )
        return {
            "final_reply": reply,
            "final_status": "escalate",
            "note": "Issue requires human technician triage.",
            "mode": "rule_fallback",
        }

    # LLM-based response generation (with conversation history if available)
    llm = get_llm_provider(allow_fallback=True)
    knowledge_context = ""
    if docs:
        knowledge_context = "\n\n".join([f"Source: {d.get('title')}\nContent: {d.get('content')}" for d in docs])

    system_prompt = (
        "You are ServiceDesk-AI, an enterprise IT support assistant. "
        "Provide helpful, clear, step-by-step troubleshooting instructions. "
        "Do not invent facts or claim to have fixed user systems unless verified. "
        "Ground your advice in the provided IT knowledge context if available."
    )
    user_prompt = ""
    if history_text:
        user_prompt += f"{history_text}\n\n"
    user_prompt += f"User Question: {message}\n"
    if knowledge_context:
        user_prompt += f"\nReference Knowledge:\n{knowledge_context}\n"

    try:
        llm_resp = llm.generate(prompt=user_prompt, system_instruction=system_prompt)
        reply_content = llm_resp.content
        # Report the real execution mode — never label mock as live
        if llm_resp.is_mock:
            note_text = f"[Demo/Mock Mode] Generated by mock provider ({llm_resp.model})"
            exec_mode = "mock"
        else:
            note_text = f"Generated by {llm_resp.provider} ({llm_resp.model})"
            exec_mode = llm_resp.provider  # e.g. "gemini", "openai", "ollama"
    except Exception as e:
        logger.error(f"LLM generation failed: {e}")
        reply_content = (
            f"Here are troubleshooting steps for your {triage.get('category', 'IT')} issue:\n"
            "1. Check connectivity and credentials.\n"
            "2. Restart the affected application or device.\n"
            "3. If unresolved, our support desk will open a ticket for you."
        )
        note_text = "Fallback troubleshooting steps (LLM error)."
        exec_mode = "rule_fallback"

    return {
        "final_reply": reply_content,
        "final_status": "answered",
        "note": note_text,
        "mode": exec_mode,
    }


def ticket_creation_node(state: ServiceDeskState) -> Dict[str, Any]:
    """
    Ticket creation node: creates a support ticket when the issue warrants it.

    Creates a ticket when:
    - Escalation is required (unknown/security/unresolved category)
    - The user explicitly asks to create/open/raise a ticket
    - No existing ticket has been created in this workflow run (deduplication)
    """
    # Deduplication: only create once per workflow run
    if state.get("ticket_created_id"):
        return {}

    message = state.get("message", "").lower()
    triage = state.get("triage", {})
    category = triage.get("category", "general")
    escalation_needed = state.get("escalation_needed", False)
    is_security = state.get("is_security_incident", False)

    # Detect explicit ticket creation intent
    explicit_request = _detect_ticket_intent(message)

    # Only create ticket for escalations, security incidents, or explicit requests
    should_create = explicit_request or escalation_needed or is_security

    if not should_create:
        return {}

    db = SessionLocal()
    try:
        user_id = state.get("user_id")
        user = db.query(User).filter(User.id == user_id).first() if user_id else None

        priority_val = triage.get("priority")
        if isinstance(priority_val, str):
            from app.models.orm import TicketPriority
            try:
                priority_val = TicketPriority(priority_val)
            except Exception:
                priority_val = None

        original_message = state.get("message", "No description provided.")
        title = original_message[:100] if len(original_message) > 5 else f"IT Support Request — {category.title()}"

        ticket_in = TicketCreate(
            title=title,
            description=original_message,
            category=category,
            subcategory=triage.get("subcategory"),
            priority=priority_val,
            impact=triage.get("impact", "Medium"),
            urgency=triage.get("urgency", "Medium"),
            assigned_group=triage.get("suggested_group", "End User Support"),
            conversation_id=state.get("conversation_id"),
        )
        ticket = create_ticket(db, ticket_in, creator=user)
        logger.info(f"[Ticket Creation] Created ticket {ticket.id} for conversation {state.get('conversation_id')}")
        return {"ticket_created_id": ticket.id}
    except Exception as e:
        logger.error(f"[Ticket Creation] Failed: {e}")
        return {}
    finally:
        db.close()


def verification_node(state: ServiceDeskState) -> Dict[str, Any]:
    """Verification node: saves assistant reply to conversation history and marks workflow terminal."""
    logger.debug(f"[Workflow Verification] Validated final state for conversation {state.get('conversation_id')}")

    final_reply = state.get("final_reply", "")
    conversation_id = state.get("conversation_id")

    if final_reply and conversation_id:
        db = SessionLocal()
        try:
            save_message(
                db=db,
                conversation_id=conversation_id,
                role="assistant",
                content=final_reply,
                user_id=state.get("user_id"),
            )
        except Exception as e:
            logger.warning(f"[Verification] Failed to save assistant reply: {e}")
        finally:
            db.close()

    return {
        "is_terminal": True,
    }


# ---------------------------------------------------------------------------
# Routing Edges
# ---------------------------------------------------------------------------

def route_after_triage(state: ServiceDeskState) -> str:
    """Route to security escalation if security incident detected, else RAG retrieval."""
    if state.get("is_security_incident"):
        return "security_escalation"
    return "rag_retrieval"


def route_after_action_decision(state: ServiceDeskState) -> str:
    """Route to action execution if an action was requested, else direct response generation."""
    if state.get("action_requested"):
        return "action_execution"
    return "response_generation"


# ---------------------------------------------------------------------------
# Graph Builder
# ---------------------------------------------------------------------------

def build_servicedesk_graph() -> StateGraph:
    """Construct and compile the LangGraph StateGraph workflow."""
    builder = StateGraph(ServiceDeskState)

    # Add Nodes
    builder.add_node("intake", intake_node)
    builder.add_node("triage", triage_node)
    builder.add_node("security_escalation", security_escalation_node)
    builder.add_node("rag_retrieval", rag_retrieval_node)
    builder.add_node("action_decision", action_decision_node)
    builder.add_node("action_execution", action_execution_node)
    builder.add_node("response_generation", response_generation_node)
    builder.add_node("ticket_creation", ticket_creation_node)
    builder.add_node("verification", verification_node)

    # Add Edges
    builder.add_edge(START, "intake")
    builder.add_edge("intake", "triage")

    builder.add_conditional_edges(
        "triage",
        route_after_triage,
        {
            "security_escalation": "security_escalation",
            "rag_retrieval": "rag_retrieval",
        },
    )

    builder.add_edge("security_escalation", "ticket_creation")
    builder.add_edge("rag_retrieval", "action_decision")

    builder.add_conditional_edges(
        "action_decision",
        route_after_action_decision,
        {
            "action_execution": "action_execution",
            "response_generation": "response_generation",
        },
    )

    builder.add_edge("action_execution", "response_generation")
    builder.add_edge("response_generation", "ticket_creation")
    builder.add_edge("ticket_creation", "verification")
    builder.add_edge("verification", END)

    return builder.compile()


# Global compiled workflow instance
_compiled_graph = None


def get_workflow_graph():
    """Retrieve singleton compiled graph."""
    global _compiled_graph
    if _compiled_graph is None:
        logger.info("Compiling LangGraph multi-agent workflow...")
        _compiled_graph = build_servicedesk_graph()
    return _compiled_graph


def reset_workflow_graph():
    """Force recompile on next call. Used in tests when environment changes."""
    global _compiled_graph
    _compiled_graph = None


def run_servicedesk_workflow(
    message: str,
    conversation_id: Optional[str] = None,
    user: Optional[User] = None,
) -> ServiceDeskState:
    """Execute the compiled LangGraph workflow end-to-end."""
    graph = get_workflow_graph()
    conv_id = conversation_id or f"CONV-{uuid.uuid4().hex[:8].upper()}"

    initial_state: ServiceDeskState = {
        "message": message,
        "conversation_id": conv_id,
        "user_id": user.id if user else None,
        "username": user.username if user else None,
        "user_role": user.role.value if user and hasattr(user.role, "value") else (str(user.role) if user else None),
        "triage": {},
        "is_security_incident": False,
        "conversation_history": "",
        "retrieved_docs": [],
        "citations": [],
        "action_requested": None,
        "action_result": None,
        "approval_needed": False,
        "approval_id": None,
        "escalation_needed": False,
        "escalation_reason": None,
        "ticket_created_id": None,
        "final_reply": "",
        "final_status": "answered",
        "note": "",
        "mode": "live",
        "iteration_count": 0,
        "is_terminal": False,
    }

    final_state = graph.invoke(initial_state)
    return final_state
