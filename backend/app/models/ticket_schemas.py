"""
Pydantic schemas for Tickets, Ticket Status, Approvals, and Audit Events.
"""

from datetime import datetime
from typing import Optional, List, Any, Dict
from pydantic import BaseModel, Field, ConfigDict
from app.models.orm import TicketPriority, TicketStatus, ApprovalStatus, RiskLevel


# --- Ticket Schemas ---

class TicketCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=200)
    description: str = Field(..., min_length=5)
    category: str = Field(default="general")
    subcategory: Optional[str] = None
    priority: Optional[TicketPriority] = TicketPriority.P3
    impact: Optional[str] = "Medium"
    urgency: Optional[str] = "Medium"
    assigned_group: Optional[str] = "End User Support"
    conversation_id: Optional[str] = None


class TicketUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    subcategory: Optional[str] = None
    priority: Optional[TicketPriority] = None
    impact: Optional[str] = None
    urgency: Optional[str] = None
    assigned_group: Optional[str] = None


class TicketAssignRequest(BaseModel):
    assignee_id: Optional[int] = None
    assigned_group: Optional[str] = None


class TicketStatusUpdate(BaseModel):
    status: TicketStatus
    notes: Optional[str] = None


class TicketResolveRequest(BaseModel):
    resolution_notes: str = Field(..., min_length=3)


class TicketEscalateRequest(BaseModel):
    reason: str = Field(..., min_length=3)
    target_group: Optional[str] = "Tier-2 Operations"


class TicketCloseRequest(BaseModel):
    notes: Optional[str] = None


class TicketReopenRequest(BaseModel):
    notes: Optional[str] = None


class TicketStatusHistoryOut(BaseModel):
    id: int
    ticket_id: str
    old_status: Optional[str]
    new_status: str
    changed_by_id: Optional[int]
    notes: Optional[str]
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)


class TicketOut(BaseModel):
    id: str
    title: str
    description: str
    category: str
    subcategory: Optional[str]
    priority: TicketPriority
    impact: str
    urgency: str
    status: TicketStatus
    assigned_group: Optional[str]
    creator_id: Optional[int]
    assignee_id: Optional[int]
    conversation_id: Optional[str]
    resolution_notes: Optional[str]
    is_escalated: bool = False
    escalation_reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TicketDetailOut(TicketOut):
    status_history: List[TicketStatusHistoryOut] = []


# --- Approval Schemas ---

class ApprovalRequestCreate(BaseModel):
    action_name: str
    action_params: Optional[Dict[str, Any]] = None
    ticket_id: Optional[str] = None
    conversation_id: Optional[str] = None
    risk_level: RiskLevel = RiskLevel.MEDIUM
    reason: str


class ApprovalDecisionRequest(BaseModel):
    decision: str = Field(..., description="'APPROVED' or 'REJECTED'")
    decision_notes: Optional[str] = None


class ApprovalRequestOut(BaseModel):
    id: str
    ticket_id: Optional[str]
    conversation_id: Optional[str]
    action_name: str
    action_params: Optional[str]
    requester_id: Optional[int]
    risk_level: RiskLevel
    reason: str
    status: ApprovalStatus
    approver_id: Optional[int]
    decision_notes: Optional[str]
    created_at: datetime
    decided_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


# --- Audit Schemas ---

class AuditEventOut(BaseModel):
    id: int
    event_type: str
    actor_id: Optional[int]
    actor_username: Optional[str]
    target_type: Optional[str]
    target_id: Optional[str]
    details: Optional[str]
    ip_address: Optional[str]
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)
