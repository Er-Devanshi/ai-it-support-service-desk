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
    TicketStatus.PENDING_APPROVAL: [TicketStatus.IN_PROGRESS, TicketStatus.RESOLVED, TicketStatus.ESCALATED, TicketStatus.CLOSED],
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


def list_tickets(
    db: Session,
    user: Optional[User] = None,
    status_filter: Optional[TicketStatus] = None,
    priority_filter: Optional[TicketPriority] = None,
    category_filter: Optional[str] = None,
    needing_escalation: Optional[bool] = None,
    skip: int = 0,
    limit: int = 50,
) -> List[Ticket]:
    """List tickets authorized for the calling user with optional filtering."""
    if user is None:
        return []

    query = db.query(Ticket)
    user_role = user.role if isinstance(user.role, UserRole) else UserRole(user.role)
    if user_role == UserRole.EMPLOYEE:
        query = query.filter(Ticket.creator_id == user.id)

    if status_filter:
        query = query.filter(Ticket.status == status_filter)
    if priority_filter:
        query = query.filter(Ticket.priority == priority_filter)
    if category_filter:
        query = query.filter(Ticket.category == category_filter)

    all_tickets = query.order_by(Ticket.created_at.desc()).all()

    if needing_escalation is not None:
        filtered = []
        for t in all_tickets:
            is_cand, _ = is_escalation_candidate(t)
            if is_cand == needing_escalation:
                filtered.append(t)
        return filtered[skip : skip + limit]

    return all_tickets[skip : skip + limit]


def update_ticket_status(
    db: Session,
    ticket_id: str,
    new_status: TicketStatus,
    user: Optional[User] = None,
    notes: Optional[str] = None,
) -> Ticket:
    """Enforce valid status transitions, RBAC permissions, and persist status history."""
    ticket = get_ticket(db, ticket_id, user)

    # Permission check for status change
    if user:
        user_role = user.role if isinstance(user.role, UserRole) else UserRole(user.role)
        if user_role == UserRole.EMPLOYEE:
            # Employees may only close their own tickets or reopen resolved/closed tickets back to IN_PROGRESS
            if new_status == TicketStatus.CLOSED:
                pass
            elif new_status == TicketStatus.IN_PROGRESS and ticket.status in (TicketStatus.RESOLVED, TicketStatus.CLOSED):
                pass
            else:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Employees may only close their tickets or reopen resolved/closed tickets.",
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


def close_ticket(
    db: Session,
    ticket_id: str,
    user: Optional[User] = None,
    notes: Optional[str] = None,
) -> Ticket:
    """Close a ticket and record status history."""
    return update_ticket_status(
        db=db,
        ticket_id=ticket_id,
        new_status=TicketStatus.CLOSED,
        user=user,
        notes=notes or "Ticket closed",
    )


def reopen_ticket(
    db: Session,
    ticket_id: str,
    user: Optional[User] = None,
    notes: Optional[str] = None,
) -> Ticket:
    """Reopen a resolved or closed ticket back to IN_PROGRESS."""
    return update_ticket_status(
        db=db,
        ticket_id=ticket_id,
        new_status=TicketStatus.IN_PROGRESS,
        user=user,
        notes=notes or "Ticket reopened for further investigation",
    )


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


def escalate_ticket(
    db: Session,
    ticket_id: str,
    reason: str,
    target_group: str = "Tier-2 Operations",
    user: Optional[User] = None,
) -> Ticket:
    """Escalate ticket to a higher tier group with reason and record audit event."""
    ticket = get_ticket(db, ticket_id, user)
    old_group = ticket.assigned_group
    ticket.assigned_group = target_group
    updated = update_ticket_status(
        db,
        ticket_id,
        TicketStatus.ESCALATED,
        user,
        notes=f"Escalated to {target_group}: {reason}",
    )
    log_audit_event(
        db=db,
        event_type="TICKET_ESCALATED",
        actor=user,
        target_type="ticket",
        target_id=ticket_id,
        details={
            "reason": reason,
            "target_group": target_group,
            "old_group": old_group,
            "priority": ticket.priority.value,
        },
    )
    return updated


def is_escalation_candidate(ticket: Ticket) -> tuple[bool, Optional[str]]:
    """
    Determine if a ticket requires escalation.
    Criteria:
    - Ticket is in OPEN or IN_PROGRESS (not already ESCALATED, RESOLVED, or CLOSED).
    - Critical priority P1 incidents.
    - Security category tickets not yet assigned to Security Operations.
    """
    if ticket.status in (TicketStatus.ESCALATED, TicketStatus.RESOLVED, TicketStatus.CLOSED):
        return False, None

    if ticket.priority == TicketPriority.P1:
        return True, "Critical P1 incident requires immediate escalation."

    if ticket.category == "security" and ticket.assigned_group != "Security Operations":
        return True, "Security incident requires escalation to Security Operations."

    return False, None


def get_tickets_needing_escalation(
    db: Session,
    user: Optional[User] = None,
    skip: int = 0,
    limit: int = 50,
) -> List[Ticket]:
    """
    Identify high-priority or unresolved tickets that require escalation.
    Restricted to Support Agents and Admins.
    """
    if user:
        user_role = user.role if isinstance(user.role, UserRole) else UserRole(user.role)
        if user_role == UserRole.EMPLOYEE:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Employees may not view queue-wide escalation candidates.",
            )

    candidates = (
        db.query(Ticket)
        .filter(Ticket.status.in_([TicketStatus.OPEN, TicketStatus.IN_PROGRESS]))
        .order_by(Ticket.created_at.asc())
        .all()
    )
    results = []
    for tkt in candidates:
        needs_esc, _ = is_escalation_candidate(tkt)
        if needs_esc:
            results.append(tkt)
    return results[skip : skip + limit]


def auto_escalate_qualifying_tickets(
    db: Session,
    user: Optional[User] = None,
) -> List[Ticket]:
    """
    Identify and systematically escalate all open high-priority/security tickets.
    """
    to_escalate = get_tickets_needing_escalation(db, user=user, skip=0, limit=100)
    escalated_tickets = []
    for tkt in to_escalate:
        _, reason = is_escalation_candidate(tkt)
        target_group = "Security Operations" if tkt.category == "security" else "Tier-2 Operations"
        updated = escalate_ticket(
            db=db,
            ticket_id=tkt.id,
            reason=reason or "Automated escalation for high-priority/unresolved incident",
            target_group=target_group,
            user=user,
        )
        escalated_tickets.append(updated)
    return escalated_tickets
