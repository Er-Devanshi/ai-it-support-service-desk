"""
State definition for LangGraph Multi-Agent Orchestration.
Maintains typed state across workflow nodes.
"""

from typing import TypedDict, Optional, List, Dict, Any


class ServiceDeskState(TypedDict):
    """Explicit state passed across LangGraph nodes."""
    message: str
    conversation_id: str
    user_id: Optional[int]
    username: Optional[str]
    user_role: Optional[str]
    
    # Triage and classification
    triage: Dict[str, Any]
    is_security_incident: bool
    
    # Conversation history (loaded at intake for multi-turn context)
    conversation_history: str
    
    # RAG knowledge
    retrieved_docs: List[Dict[str, Any]]
    citations: List[Dict[str, Any]]
    
    # Actions & Tool calling
    action_requested: Optional[Dict[str, Any]]
    action_result: Optional[Dict[str, Any]]
    approval_needed: bool
    approval_id: Optional[str]
    
    # Escalation
    escalation_needed: bool
    escalation_reason: Optional[str]
    
    # Tickets
    ticket_created_id: Optional[str]
    
    # Response synthesis
    final_reply: str
    final_status: str  # 'answered' | 'escalate' | 'unknown' | 'pending_approval'
    note: str
    mode: str
    
    # Guardrails
    iteration_count: int
    is_terminal: bool
