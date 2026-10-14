"""
Persistent Ticket Lifecycle Management Service for ServiceDesk-AI.
Enforces valid status transitions, RBAC visibility, audit logging,
and status history persistence.
"""

from datetime import datetime, timezone
import uuid
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.orm import (
    Ticket,
    TicketStatus,
    TicketPriority,
    TicketStatusHistory,
    User,
    UserRole,
)
from app.models.ticket_schemas import TicketCreate, TicketUpdate
from app.services.audit_service import log_audit_event
from app.utils.logger import logger

# Valid lifecycle status transitions
VALID_TRANSITIONS: Dict[TicketStatus, List[TicketStatus]] = {
    TicketStatus.OPEN: [TicketStatus.IN_PROGRESS, TicketStatus.ESCALATED, TicketStatus.CLOSED],
    TicketStatus.IN_PROGRESS: [TicketStatus.PENDING_APPROVAL, TicketStatus.RESOLVED, TicketStatus.ESCALATED, TicketStatus.CLOSED],
    TicketStatus.PENDING_APPROVAL: [TicketStatus.IN_PROGRESS, TicketStatus.RESOLVED, TicketStatus.ESCALATED],
    TicketStatus.RESOLVED: [TicketStatus.CLOSED, TicketStatus.IN_PROGRESS],  # In-progress means reopened
    TicketStatus.ESCALATED: [TicketStatus.IN_PROGRESS, TicketStatus.RESOLVED, TicketStatus.CLOSED],
    TicketStatus.CLOSED: [TicketStatus.IN_PROGRESS],  # Reopening closed ticket
}


def create_ticket(
    db: Session,
    ticket_in: TicketCreate,
    creator: Optional[User] = None,
) -> Ticket:
    """Create a new ticket and record initial status history."""
    ticket_id = f"TKT-{uuid.uuid4().hex[:6].upper()}"
    ticket = Ticket(
        id=ticket_id,
        title=ticket_in.title,
        description=ticket_in.description,
        category=ticket_in.category,
        subcategory=ticket_in.subcategory,
        priority=ticket_in.priority or TicketPriority.P3,
        impact=ticket_in.impact or "Medium",
        urgency=ticket_in.urgency or "Medium",
        status=TicketStatus.OPEN,
        assigned_group=ticket_in.assigned_group or "End User Support",
        creator_id=creator.id if creator else None,
        conversation_id=ticket_in.conversation_id,
    )
    db.add(ticket)
    db.flush()

    # Record initial history
    history = TicketStatusHistory(
        ticket_id=ticket_id,
        old_status=None,
        new_status=TicketStatus.OPEN.value,
        changed_by_id=creator.id if creator else None,
        notes="Ticket created",
    )
    db.add(history)
    db.commit()
    db.refresh(ticket)

    log_audit_event(
        db=db,
        event_type="TICKET_CREATED",
        actor=creator,
        target_type="ticket",
        target_id=ticket_id,
        details={"title": ticket.title, "priority": ticket.priority.value, "category": ticket.category},
    )
    logger.info(f"Created ticket {ticket_id} ('{ticket.title}')")
    return ticket


def get_ticket(db: Session, ticket_id: str, user: Optional[User] = None) -> Ticket:
    """Retrieve a ticket by ID, enforcing RBAC ownership checks for employees."""
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Ticket '{ticket_id}' not found")

    if user:
        user_role = user.role if isinstance(user.role, UserRole) else UserRole(user.role)
        if user_role == UserRole.EMPLOYEE and ticket.creator_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not authorized to view this ticket.",
            )
    return ticket


def list_tickets(db: Session, user: Optional[User] = None, skip: int = 0, limit: int = 50) -> List[Ticket]:
    """List tickets authorized for the calling user."""
    query = db.query(Ticket)
    if user:
        user_role = user.role if isinstance(user.role, UserRole) else UserRole(user.role)
        if user_role == UserRole.EMPLOYEE:
            query = query.filter(Ticket.creator_id == user.id)
    return query.order_by(Ticket.created_at.desc()).offset(skip).limit(limit).all()


def update_ticket_status(
    db: Session,
    ticket_id: str,
    new_status: TicketStatus,
    user: Optional[User] = None,
    notes: Optional[str] = None,
) -> Ticket:
    """Enforce valid status transitions and persist status history."""
    ticket = get_ticket(db, ticket_id, user)

    # Permission check for status change
    if user:
        user_role = user.role if isinstance(user.role, UserRole) else UserRole(user.role)
        if user_role == UserRole.EMPLOYEE and new_status not in (TicketStatus.CLOSED, TicketStatus.IN_PROGRESS):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Employees may only close or reopen their own tickets.",
            )

    current_status = ticket.status
    if new_status == current_status:
        return ticket

    allowed_next = VALID_TRANSITIONS.get(current_status, [])
    if new_status not in allowed_next:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status transition: Cannot move ticket from '{current_status.value}' to '{new_status.value}'. Allowed: {[s.value for s in allowed_next]}",
        )

    old_status_val = ticket.status.value
    ticket.status = new_status
    ticket.updated_at = datetime.now(timezone.utc)

    # Persist history entry
    history = TicketStatusHistory(
        ticket_id=ticket_id,
        old_status=old_status_val,
        new_status=new_status.value,
        changed_by_id=user.id if user else None,
        notes=notes or f"Status changed from {old_status_val} to {new_status.value}",
    )
    db.add(history)
    db.commit()
    db.refresh(ticket)

    log_audit_event(
        db=db,
        event_type="TICKET_STATUS_UPDATED",
        actor=user,
        target_type="ticket",
        target_id=ticket_id,
        details={"old_status": old_status_val, "new_status": new_status.value, "notes": notes},
    )
    return ticket


def assign_ticket(
    db: Session,
    ticket_id: str,
    assignee_id: Optional[int] = None,
    assigned_group: Optional[str] = None,
    user: Optional[User] = None,
) -> Ticket:
    """Assign ticket to a support agent or group."""
    ticket = get_ticket(db, ticket_id, user)

    if user:
        user_role = user.role if isinstance(user.role, UserRole) else UserRole(user.role)
        if user_role not in (UserRole.SUPPORT_AGENT, UserRole.ADMIN):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only Support Agents or Admins may assign tickets.")

    if assignee_id is not None:
        assignee = db.query(User).filter(User.id == assignee_id).first()
        if not assignee:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignee user not found")
        ticket.assignee_id = assignee_id

    if assigned_group:
        ticket.assigned_group = assigned_group

    ticket.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(ticket)

    log_audit_event(
        db=db,
        event_type="TICKET_ASSIGNED",
        actor=user,
        target_type="ticket",
        target_id=ticket_id,
        details={"assignee_id": assignee_id, "assigned_group": assigned_group},
    )
    return ticket


def resolve_ticket(db: Session, ticket_id: str, resolution_notes: str, user: Optional[User] = None) -> Ticket:
    """Mark ticket as RESOLVED with required resolution notes."""
    ticket = get_ticket(db, ticket_id, user)
    ticket.resolution_notes = resolution_notes
    return update_ticket_status(db, ticket_id, TicketStatus.RESOLVED, user, notes=f"Resolved: {resolution_notes}")


def escalate_ticket(db: Session, ticket_id: str, reason: str, target_group: str = "Tier-2 Operations", user: Optional[User] = None) -> Ticket:
    """Escalate ticket to a higher tier group with reason."""
    ticket = get_ticket(db, ticket_id, user)
    ticket.assigned_group = target_group
    return update_ticket_status(db, ticket_id, TicketStatus.ESCALATED, user, notes=f"Escalated to {target_group}: {reason}")
