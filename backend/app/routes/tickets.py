"""
Ticket management routes for ServiceDesk-AI.
Implements full REST lifecycle operations with RBAC and validation.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.orm import User, UserRole, Ticket
from app.models.ticket_schemas import (
    TicketCreate,
    TicketUpdate,
    TicketOut,
    TicketDetailOut,
    TicketAssignRequest,
    TicketStatusUpdate,
    TicketResolveRequest,
    TicketEscalateRequest,
    TicketStatusHistoryOut,
)
from app.services.auth_service import get_current_user, get_current_user_optional, require_roles
from app.services.ticket_service import (
    create_ticket,
    get_ticket,
    list_tickets,
    update_ticket_status,
    assign_ticket,
    resolve_ticket,
    escalate_ticket,
)

router = APIRouter(prefix="/tickets", tags=["Tickets"])


@router.post("", response_model=TicketOut, status_code=status.HTTP_201_CREATED)
def create_new_ticket(
    ticket_in: TicketCreate,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """Create a new IT support ticket."""
    return create_ticket(db, ticket_in, creator=current_user)


@router.get("", response_model=List[TicketOut])
def get_all_tickets(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """
    List tickets.
    Employees see only their own tickets; Support Agents and Admins see all tickets.
    """
    return list_tickets(db, user=current_user, skip=skip, limit=limit)


@router.get("/{ticket_id}", response_model=TicketDetailOut)
def get_ticket_by_id(
    ticket_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """Retrieve ticket details including status history."""
    ticket = get_ticket(db, ticket_id, user=current_user)
    return ticket


@router.patch("/{ticket_id}", response_model=TicketOut)
def update_ticket_fields(
    ticket_id: str,
    ticket_update: TicketUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update permitted ticket fields."""
    ticket = get_ticket(db, ticket_id, user=current_user)

    for field, val in ticket_update.model_dump(exclude_unset=True).items():
        if val is not None:
            setattr(ticket, field, val)

    db.commit()
    db.refresh(ticket)
    return ticket


@router.post("/{ticket_id}/assign", response_model=TicketOut)
def assign_ticket_route(
    ticket_id: str,
    assign_in: TicketAssignRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.SUPPORT_AGENT, UserRole.ADMIN])),
):
    """Assign ticket to a support agent or assignment group (Support Agent or Admin only)."""
    return assign_ticket(
        db,
        ticket_id=ticket_id,
        assignee_id=assign_in.assignee_id,
        assigned_group=assign_in.assigned_group,
        user=current_user,
    )


@router.post("/{ticket_id}/status", response_model=TicketOut)
def update_status_route(
    ticket_id: str,
    status_in: TicketStatusUpdate,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """Update ticket status, enforcing valid lifecycle transitions."""
    return update_ticket_status(
        db,
        ticket_id=ticket_id,
        new_status=status_in.status,
        user=current_user,
        notes=status_in.notes,
    )


@router.post("/{ticket_id}/resolve", response_model=TicketOut)
def resolve_ticket_route(
    ticket_id: str,
    resolve_in: TicketResolveRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.SUPPORT_AGENT, UserRole.ADMIN])),
):
    """Mark ticket as resolved with required resolution notes."""
    return resolve_ticket(
        db,
        ticket_id=ticket_id,
        resolution_notes=resolve_in.resolution_notes,
        user=current_user,
    )


@router.post("/{ticket_id}/escalate", response_model=TicketOut)
def escalate_ticket_route(
    ticket_id: str,
    escalate_in: TicketEscalateRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """Escalate ticket to a higher tier group."""
    return escalate_ticket(
        db,
        ticket_id=ticket_id,
        reason=escalate_in.reason,
        target_group=escalate_in.target_group or "Tier-2 Operations",
        user=current_user,
    )


@router.get("/{ticket_id}/history", response_model=List[TicketStatusHistoryOut])
def get_ticket_history_route(
    ticket_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """Retrieve complete audit history of status transitions for a ticket."""
    ticket = get_ticket(db, ticket_id, user=current_user)
    return ticket.status_history
