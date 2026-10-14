"""
Chat service for ServiceDesk-AI.
Upgraded to use LangGraph multi-agent orchestration while preserving
the existing POST /api/chat contract and keyword response compatibility.
"""

from typing import Optional
from app.models.chat import ChatResponse
from app.models.orm import User
from app.services.workflow.graph import run_servicedesk_workflow


def process_message(
    message: str,
    conversation_id: Optional[str] = None,
    user: Optional[User] = None,
) -> ChatResponse:
    """
    Process an incoming support message via the LangGraph Multi-Agent workflow.
    
    Preserves complete compatibility with Phase 1 fields:
      - reply: str
      - category: str
      - status: str
      - note: str
    While adding rich metadata fields for conversational context, triage,
    citations, approvals, and actions.
    """
    state = run_servicedesk_workflow(
        message=message,
        conversation_id=conversation_id,
        user=user,
    )

    triage = state.get("triage", {})
    category = triage.get("category", "unknown")
    priority_val = triage.get("priority")
    if hasattr(priority_val, "value"):
        priority_val = priority_val.value

    return ChatResponse(
        reply=state.get("final_reply", ""),
        category=category,
        status=state.get("final_status", "answered"),
        note=state.get("note", "Processed via LangGraph Multi-Agent Workflow"),
        conversation_id=state.get("conversation_id"),
        priority=priority_val,
        ticket_id=state.get("ticket_created_id"),
        escalated=state.get("escalation_needed", False),
        requires_approval=state.get("approval_needed", False),
        approval_id=state.get("approval_id"),
        action_executed=state.get("action_result"),
        citations=state.get("citations", []),
        mode=state.get("mode", "live"),
    )
