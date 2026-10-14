"""
Pydantic models for the chat endpoint.

Maintains complete backward compatibility with Phase 1 contracts
while enriching response attributes with agent orchestration,
triage priority, ticket IDs, approval requests, and citations.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Body expected by POST /api/chat."""

    message: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="The user's IT support question or problem description.",
        examples=["My Wi-Fi is not working"],
    )
    conversation_id: Optional[str] = Field(
        default=None,
        description="Optional conversation identifier to maintain multi-turn context.",
    )


class Citation(BaseModel):
    source: str
    title: str
    snippet: str
    relevance_score: Optional[float] = None


class ChatResponse(BaseModel):
    """Body returned by POST /api/chat."""

    reply: str = Field(description="The support response text shown to the user.")
    category: str = Field(description="Detected IT issue category (e.g. 'network', 'account').")
    status: str = Field(description="Handling status: 'answered' | 'escalate' | 'unknown' | 'pending_approval'.")
    note: str = Field(description="Internal note, system mode, or limitation disclosure.")
    
    # Extended attributes for multi-agent, triage, RAG, and IT actions
    conversation_id: Optional[str] = Field(default=None, description="Conversation session ID")
    priority: Optional[str] = Field(default=None, description="Triage priority (P1, P2, P3, P4)")
    ticket_id: Optional[str] = Field(default=None, description="Auto-created or referenced ticket ID if applicable")
    escalated: bool = Field(default=False, description="Flag indicating if the issue was escalated")
    requires_approval: bool = Field(default=False, description="Flag indicating if an IT action requires human approval")
    approval_id: Optional[str] = Field(default=None, description="ID of generated approval request if pending")
    action_executed: Optional[Dict[str, Any]] = Field(default=None, description="Details of simulated action if executed")
    citations: List[Dict[str, Any]] = Field(default_factory=list, description="Retrieved knowledge base citations")
    mode: Optional[str] = Field(default="live", description="Execution mode: 'gemini', 'mock', 'rule_fallback'")
