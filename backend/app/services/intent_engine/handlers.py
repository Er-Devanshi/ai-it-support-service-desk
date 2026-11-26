"""
Intent Handlers for ServiceDesk-AI.

Each handler receives the LangGraph state dict and returns a partial-state
update (same contract as every other node).  Replies are written to
final_reply / final_status so they flow through response_generation and
verification nodes normally, ensuring conversation history is saved.

Handlers:
  handle_greeting    - short friendly reply, no ticket
  handle_thanks      - short acknowledgement, no ticket
  handle_goodbye     - short farewell, no ticket
  handle_check_ticket_status - list user's tickets (RBAC-enforced)
  handle_create_ticket - create ticket using triage data already in state
"""

from typing import Dict, Any, Optional, List

from app.db.session import SessionLocal
from app.models.orm import User, UserRole, Ticket
from app.services.ticket_service import list_tickets, create_ticket
from app.services.audit_service import log_audit_event
from app.models.ticket_schemas import TicketCreate
from app.utils.logger import logger


# ---------------------------------------------------------------------------
# Small talk handlers
# ---------------------------------------------------------------------------

def handle_greeting(state: Dict[str, Any]) -> Dict[str, Any]:
    """Return a friendly greeting asking the user to describe their IT issue."""
    username = state.get("username") or "there"
    reply = (
        f"👋 Hello, {username}! I'm ServiceDesk AI, your IT support assistant.\n\n"
        "How can I help you today? Please describe your IT issue and I'll get right on it."
    )
    return {
        "final_reply": reply,
        "final_status": "answered",
        "note": "Intent: greeting — handled directly.",
        "mode": "intent_engine",
    }


def handle_thanks(state: Dict[str, Any]) -> Dict[str, Any]:
    """Acknowledge thanks warmly."""
    reply = (
        "You're very welcome! 😊 If you run into any other IT issues, "
        "don't hesitate to ask. I'm here to help."
    )
    return {
        "final_reply": reply,
        "final_status": "answered",
        "note": "Intent: thanks — handled directly.",
        "mode": "intent_engine",
    }


def handle_goodbye(state: Dict[str, Any]) -> Dict[str, Any]:
    """Send a friendly farewell."""
    reply = (
        "Goodbye! 👋 Take care, and feel free to reach out any time you need IT support."
    )
    return {
        "final_reply": reply,
        "final_status": "answered",
        "note": "Intent: goodbye — handled directly.",
        "mode": "intent_engine",
    }


# ---------------------------------------------------------------------------
# Ticket status handler
# ---------------------------------------------------------------------------

def handle_check_ticket_status(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    List the calling user's tickets.

    - Unauthenticated users → "please log in" message.
    - Employees see ONLY their own tickets (enforced by list_tickets).
    - Support agents / admins see all tickets they're authorised to see.
    - Writes an audit event TICKET_STATUS_CHECKED.
    """
    user_id: Optional[int] = state.get("user_id")
    username: Optional[str] = state.get("username")
    user_role_str: Optional[str] = state.get("user_role")

    # Unauthenticated
    if user_id is None:
        return {
            "final_reply": (
                "🔒 Please log in to see your tickets.\n\n"
                "You can sign in using the button in the top-right corner of the UI."
            ),
            "final_status": "answered",
            "note": "Intent: check_ticket_status — unauthenticated user.",
            "mode": "intent_engine",
        }

    db = SessionLocal()
    try:
        # Reconstruct user object for RBAC
        user: Optional[User] = db.query(User).filter(User.id == user_id).first()
        if user is None:
            # User ID in token but not in DB (edge case)
            return {
                "final_reply": "⚠️ Your user account could not be found. Please log in again.",
                "final_status": "answered",
                "note": "Intent: check_ticket_status — user not found in DB.",
                "mode": "intent_engine",
            }

        # list_tickets enforces RBAC internally (employees only see own tickets)
        tickets: List[Ticket] = list_tickets(db, user=user, limit=10)

        # Write audit event
        log_audit_event(
            db=db,
            event_type="TICKET_STATUS_CHECKED",
            actor=user,
            target_type="ticket_list",
            target_id=None,
            details={"ticket_count": len(tickets)},
        )

        if not tickets:
            reply = (
                "📋 You don't have any support tickets yet.\n\n"
                "If you have an IT issue, just describe it and I'll help you troubleshoot "
                "or create a ticket."
            )
        else:
            lines = [f"📋 **Your support tickets** ({len(tickets)} found):\n"]
            for t in tickets:
                priority_str = t.priority.value if hasattr(t.priority, "value") else str(t.priority)
                status_str = t.status.value if hasattr(t.status, "value") else str(t.status)
                lines.append(
                    f"• **{t.id}** — {t.title[:60]}\n"
                    f"  Status: `{status_str}` | Priority: `{priority_str}`"
                )
            if len(tickets) == 10:
                lines.append("\n_Showing the 10 most recent tickets._")
            reply = "\n".join(lines)

        return {
            "final_reply": reply,
            "final_status": "answered",
            "note": f"Intent: check_ticket_status — found {len(tickets)} ticket(s).",
            "mode": "intent_engine",
        }

    except Exception as e:
        logger.error(f"[handle_check_ticket_status] Error: {e}")
        return {
            "final_reply": (
                "⚠️ I encountered an error while retrieving your tickets. "
                "Please try again or contact support directly."
            ),
            "final_status": "answered",
            "note": f"Intent: check_ticket_status — error: {e}",
            "mode": "intent_engine",
        }
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Create-ticket handler
# ---------------------------------------------------------------------------

def handle_create_ticket(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a ticket using the category, priority and assigned_group that
    triage_node already computed — so tickets look identical to those
    created by the existing pipeline's ticket_creation_node.

    If the message is just "create a ticket" with no prior context, we
    still create the ticket with whatever triage determined (category
    defaults to 'general', P3).  The user's raw message is used as the
    description.

    Writes an audit event TICKET_CREATED (via create_ticket in ticket_service).
    """
    # Deduplication: if a ticket already exists for this workflow run, skip
    if state.get("ticket_created_id"):
        existing_id = state["ticket_created_id"]
        return {
            "final_reply": (
                f"✅ A support ticket **{existing_id}** has already been created for this session.\n\n"
                "Our team will get back to you shortly."
            ),
            "final_status": "answered",
            "note": f"Intent: create_ticket — deduplication, existing ticket {existing_id}.",
            "mode": "intent_engine",
        }

    triage: Dict[str, Any] = state.get("triage", {})
    category: str = triage.get("category", "general")
    if category == "unknown":
        category = "general"

    # Reuse priority already computed by triage_node
    priority_val = triage.get("priority")
    if isinstance(priority_val, str):
        from app.models.orm import TicketPriority
        try:
            priority_val = TicketPriority(priority_val)
        except Exception:
            priority_val = None

    impact: str = triage.get("impact", "Medium")
    urgency: str = triage.get("urgency", "Medium")
    assigned_group: str = triage.get("suggested_group", "End User Support")

    # Use original message as description; fall back to conversation history
    original_message: str = state.get("message", "No description provided.")
    conv_history: str = state.get("conversation_history", "")

    # If message is very short (just "create a ticket"), grab context from history
    if len(original_message.split()) <= 4 and conv_history:
        # Last user turn from history is a reasonable description
        description = conv_history.strip().split("\n")[-1] or original_message
    else:
        description = original_message

    title = description[:100] if len(description) > 5 else f"IT Support Request — {category.title()}"

    db = SessionLocal()
    try:
        user_id: Optional[int] = state.get("user_id")
        user: Optional[User] = None
        if user_id is not None:
            user = db.query(User).filter(User.id == user_id).first()

        ticket_in = TicketCreate(
            title=title,
            description=description,
            category=category,
            subcategory=triage.get("subcategory"),
            priority=priority_val,
            impact=impact,
            urgency=urgency,
            assigned_group=assigned_group,
            conversation_id=state.get("conversation_id"),
        )

        ticket = create_ticket(db, ticket_in, creator=user)

        if not ticket or not ticket.id:
            raise RuntimeError("create_ticket returned None or invalid ticket")

        reply = (
            f"✅ **Support ticket created!**\n\n"
            f"• **Ticket ID:** `{ticket.id}`\n"
            f"• **Category:** {category.title()}\n"
            f"• **Priority:** {ticket.priority.value}\n"
            f"• **Assigned to:** {assigned_group}\n\n"
            f"Our IT team will review your request and get back to you shortly. "
            f"You can check the status anytime by asking me \"show my tickets\"."
        )

        return {
            "final_reply": reply,
            "final_status": "answered",
            "ticket_created_id": ticket.id,
            "note": f"Intent: create_ticket — created {ticket.id}.",
            "mode": "intent_engine",
        }

    except Exception as e:
        logger.error(f"[handle_create_ticket] Error: {e}")
        return {
            "final_reply": (
                "⚠️ I wasn't able to create a ticket right now due to a system error.\n\n"
                "Please try again or use the **New Ticket** button in the Tickets tab."
            ),
            "final_status": "answered",
            "note": f"Intent: create_ticket — error: {e}",
            "mode": "intent_engine",
        }
    finally:
        db.close()
