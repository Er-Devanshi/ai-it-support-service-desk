"""
Tests for Ticket Management System, SQLite Persistence, Status Transitions, and RBAC.
"""

import pytest
from app.models.orm import TicketStatus, TicketPriority
from app.models.ticket_schemas import TicketCreate
from app.services.ticket_service import (
    create_ticket,
    get_ticket,
    update_ticket_status,
    resolve_ticket,
    list_tickets,
)
from fastapi import HTTPException


def test_ticket_creation_and_retrieval(db_session, employee_user):
    """Test 8: Ticket creation persists in database and generates unique ID."""
    tkt_in = TicketCreate(
        title="Cannot connect to corporate VPN",
        description="Error 403 when launching AnyConnect client.",
        category="network",
        priority=TicketPriority.P2,
    )
    ticket = create_ticket(db_session, tkt_in, creator=employee_user)
    
    assert ticket.id.startswith("TKT-")
    assert ticket.status == TicketStatus.OPEN
    assert ticket.creator_id == employee_user.id
    assert len(ticket.status_history) == 1
    assert ticket.status_history[0].new_status == "OPEN"

    # Retrieval
    fetched = get_ticket(db_session, ticket.id, user=employee_user)
    assert fetched.title == tkt_in.title


def test_ticket_status_valid_transitions(db_session, employee_user, agent_user):
    """Test 10a: Valid lifecycle transition: OPEN -> IN_PROGRESS -> RESOLVED."""
    tkt_in = TicketCreate(title="Printer offline", description="Office printer in 3rd floor is unresponsive.")
    ticket = create_ticket(db_session, tkt_in, creator=employee_user)

    # Move to IN_PROGRESS
    updated = update_ticket_status(db_session, ticket.id, TicketStatus.IN_PROGRESS, user=agent_user)
    assert updated.status == TicketStatus.IN_PROGRESS

    # Resolve
    resolved = resolve_ticket(db_session, ticket.id, resolution_notes="Power cycled printer and cleared jammed paper.", user=agent_user)
    assert resolved.status == TicketStatus.RESOLVED
    assert "Power cycled" in resolved.resolution_notes
    assert len(resolved.status_history) == 3


def test_ticket_status_invalid_transition_rejected(db_session, employee_user, agent_user):
    """Test 10b: Invalid transition OPEN -> RESOLVED is rejected."""
    tkt_in = TicketCreate(title="Slow laptop", description="Opening browser takes 2 minutes.")
    ticket = create_ticket(db_session, tkt_in, creator=employee_user)

    # Directly jumping from OPEN to RESOLVED is prohibited by lifecycle rules
    with pytest.raises(HTTPException) as exc_info:
        update_ticket_status(db_session, ticket.id, TicketStatus.RESOLVED, user=agent_user)
    assert exc_info.value.status_code == 400
    assert "Invalid status transition" in exc_info.value.detail


def test_ticket_rbac_visibility(db_session, employee_user, agent_user):
    """Test 11: Employees only see their own tickets, Agents see all."""
    # Create ticket for employee
    t1 = create_ticket(db_session, TicketCreate(title="T1 Employee Ticket", description="Employee ticket"), creator=employee_user)
    # Create ticket for agent
    t2 = create_ticket(db_session, TicketCreate(title="T2 Agent Ticket", description="Agent ticket"), creator=agent_user)

    # Employee views tickets
    emp_list = list_tickets(db_session, user=employee_user)
    emp_ids = [t.id for t in emp_list]
    assert t1.id in emp_ids
    assert t2.id not in emp_ids

    # Agent views tickets
    agent_list = list_tickets(db_session, user=agent_user)
    agent_ids = [t.id for t in agent_list]
    assert t1.id in agent_ids
    assert t2.id in agent_ids
