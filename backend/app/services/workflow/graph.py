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

from app.config import settings
from app.services.workflow.state import ServiceDeskState
from app.services.triage_service import TicketTriageService, TriageResult
from app.services.rag.retrieval_interface import get_retriever
from app.services.nlp.responder import build_response
from app.services.actions.action_registry import (
    get_action_definition,
    execute_action,
    ACTION_REGISTRY,
)
from app.services.approval_service import create_approval_request
from app.services.ticket_service import create_ticket, escalate_ticket, escalate_ticket_automatic
from app.services.conversation_service import (
    get_history,
    save_message,
    format_history_for_llm,
)
from app.models.ticket_schemas import TicketCreate
from app.db.session import SessionLocal
from app.models.orm import User, Ticket
from app.utils.logger import logger


# ---------------------------------------------------------------------------
# Ticket Intent Detection
# ---------------------------------------------------------------------------
def _detect_ticket_intent(message: str) -> bool:
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
    message_lower = message.lower()
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


# ---------------------------------------------------------------------------
# Node Definitions
# ---------------------------------------------------------------------------

def intake_node(state: ServiceDeskState) -> Dict[str, Any]:
    """Intake node: initializes session identifiers, loads conversation history, and saves the user message."""
    logger.debug(f"[Workflow Intake] Processing conversation {state.get('conversation_id')}")
    iterations = state.get("iteration_count", 0) + 1

    existing_ticket_id = state.get("ticket_created_id")

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

        # If ticket was not passed in state, check if conversation already has an active ticket
        if not existing_ticket_id:
            existing_ticket = db.query(Ticket).filter(Ticket.conversation_id == state["conversation_id"]).first()
            if existing_ticket:
                existing_ticket_id = existing_ticket.id
            else:
                # Check if user mentioned an existing ticket ID in their message
                tkt_match = re.search(r"\b(TKT-[A-Fa-f0-9]{6})\b", state.get("message", ""))
                if tkt_match:
                    ref_tkt = db.query(Ticket).filter(Ticket.id == tkt_match.group(1).upper()).first()
                    if ref_tkt:
                        existing_ticket_id = ref_tkt.id
    except Exception as e:
        logger.warning(f"[Intake] Conversation history operation failed: {e}")
        history_text = ""
    finally:
        db.close()

    return {
        "iteration_count": iterations,
        "is_terminal": iterations > 5,
        "conversation_history": history_text,
        "ticket_created_id": existing_ticket_id,
    }


def triage_node(state: ServiceDeskState) -> Dict[str, Any]:
    """Triage node: runs category classification, priority calculation, and security scan with conversation context."""
    message = state.get("message", "")
    context = state.get("conversation_history")
    triage_service = TicketTriageService()  # No LLM provider needed
    triage_result = triage_service.triage_message(message, context=context)

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
    """RAG node: queries retrieval interface, passing conversation context."""
    message = state.get("message", "")
    context = state.get("conversation_history")
    retriever = get_retriever()
    res = retriever.retrieve(query=message, context=context, top_k=settings.RAG_TOP_K)

    retrieved = []
    citations = []
    if res.is_available and res.documents:
        for doc in res.documents:
            retrieved.append(doc.model_dump())
            snippet = doc.content[:250].strip()
            if len(doc.content) > 250:
                snippet += "..."
            citations.append({
                "source": doc.source,
                "title": doc.title,
                "snippet": snippet,
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
                ticket_id=state.get("ticket_created_id"),
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
    """Response generation node: synthesizes troubleshooting reply from retrieved knowledge and action results.
    
    If retrieval score is weak (below threshold), asks a clarifying question instead of presenting uncertain content.
    """
    message = state.get("message", "")
    triage = state.get("triage", {})
    action_result = state.get("action_result")
    approval_id = state.get("approval_id")
    approval_needed = state.get("approval_needed")
    docs = state.get("retrieved_docs", [])
    category = triage.get("category", "general")

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

    # Check raw retrieval score (before normalization)
    # RAW score = normalized_score * 10, so threshold 0.5 means raw >= 5.0
    top_relevance_score = docs[0].get("relevance_score", 0.0) if docs else 0.0
    raw_score = top_relevance_score * 10.0  # Denormalize to get raw BM25 score
    has_strong_rag_match = raw_score >= (settings.RAG_STRONG_MATCH_THRESHOLD * 10.0)
    
    if has_strong_rag_match and docs:
        # Build response from retrieved documents using BM25 + responder
        # Convert retrieved_docs back to RetrievedChunk objects for build_response()
        from app.services.rag.retrieval_interface import RetrievedChunk
        chunks = []
        for d in docs:
            chunk = RetrievedChunk(
                chunk_id=d.get("chunk_id", ""),
                source=d.get("source", ""),
                title=d.get("title", ""),
                content=d.get("content", ""),
                relevance_score=d.get("relevance_score"),
                metadata=d.get("metadata", {}),
            )
            chunks.append(chunk)
        
        reply_content, should_escalate = build_response(
            category=category,
            retrieved_docs=chunks,
            relevance_threshold=settings.RAG_RELEVANCE_THRESHOLD,
        )
        
        note_text = f"Extractive response from {len(chunks)} retrieved documents (BM25)"
        exec_mode = "own_engine"
        
        return {
            "final_reply": reply_content,
            "final_status": "escalate" if should_escalate else "answered",
            "note": note_text,
            "mode": exec_mode,
        }
    
    # Weak match: ask clarifying question instead of uncertain answer
    reply = (
        "I'm not sure about your issue, but I can help narrow it down.\n\n"
        "To find the right guide, could you tell me:\n"
        "1. **What device or OS are you using?** (Windows, Mac, mobile, etc.)\n"
        "2. **What is the exact error message** you're seeing (if any)?\n"
        "3. **When did this start?** (today, after an update, etc.)\n\n"
        "Or, if you'd like a technician to look into this, I can create a support ticket for you. "
        "Just say **'create a ticket'** and I'll get one started."
    )
    return {
        "final_reply": reply,
        "final_status": "escalate",
        "note": "Weak retrieval match (raw BM25 < threshold): ask clarifying question instead of uncertain answer",
        "mode": "own_engine",
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
        
        if not ticket or not ticket.id:
            logger.error(f"[Ticket Creation] Failed to create ticket: ticket object is None or invalid")
            return {}

        # If escalation is required or security incident, transition newly created ticket to ESCALATED
        if escalation_needed or is_security:
            target_grp = triage.get("suggested_group") or ("Security Operations" if is_security else "Tier-2 Operations")
            esc_reason = state.get("escalation_reason") or ("Security incident detected" if is_security else "Automated escalation for technician triage")
            # Use system-level escalation function for automatic escalations (no employee RBAC check)
            ticket = escalate_ticket_automatic(
                db=db,
                ticket_id=ticket.id,
                reason=esc_reason,
                target_group=target_grp,
            )

        logger.info(f"[Ticket Creation] Created ticket {ticket.id} (Status: {ticket.status.value}) for conversation {state.get('conversation_id')}")

        # Update final reply with the specific ticket ID
        result_update: Dict[str, Any] = {"ticket_created_id": ticket.id}
        final_reply = state.get("final_reply", "")
        if "A support ticket is being created for this issue." in final_reply:
            result_update["final_reply"] = final_reply.replace(
                "A support ticket is being created for this issue.",
                f"Support ticket #{ticket.id} has been created for this issue.",
            )
        elif explicit_request and final_reply and ticket.id not in final_reply:
            result_update["final_reply"] = final_reply + f"\n\n🎫 Support ticket #{ticket.id} has been created for this issue."
        return result_update
    except Exception as e:
        logger.error(f"[Ticket Creation] Failed: {e}")
        # Do NOT claim ticket was created if it actually failed
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
    builder.add_node("triage_processing", triage_node)
    builder.add_node("security_escalation", security_escalation_node)
    builder.add_node("rag_retrieval", rag_retrieval_node)
    builder.add_node("action_decision", action_decision_node)
    builder.add_node("action_execution", action_execution_node)
    builder.add_node("response_generation", response_generation_node)
    builder.add_node("ticket_creation", ticket_creation_node)
    builder.add_node("verification", verification_node)

    # Add Edges
    builder.add_edge(START, "intake")
    builder.add_edge("intake", "triage_processing")

    builder.add_conditional_edges(
        "triage_processing",
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
