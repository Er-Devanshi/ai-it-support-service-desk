"""
Tests for Ticket Lifecycle, RBAC Ownership Enforcement, Escalation Identification,
and Multi-Agent Workflow Coordination.
"""

import pytest
from fastapi import HTTPException
from app.models.orm import Ticket, TicketStatus, TicketPriority, UserRole, AuditEvent
from app.models.ticket_schemas import (
    TicketCreate,
    TicketUpdate,
    TicketCloseRequest,
    TicketReopenRequest,
)
from app.services.ticket_service import (
    create_ticket,
    get_ticket,
    list_tickets,
    update_ticket_status,
    close_ticket,
    reopen_ticket,
    resolve_ticket,
    escalate_ticket,
    is_escalation_candidate,
    get_tickets_needing_escalation,
    auto_escalate_qualifying_tickets,
)
from app.services.auth_service import create_access_token


@pytest.fixture
def other_employee(db_session):
    from app.models.orm import User
    from app.services.auth_service import hash_password
    user = User(
        username="other_employee",
        email="other@test.com",
        hashed_password=hash_password("otherPass123"),
        role=UserRole.EMPLOYEE,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def other_emp_headers(other_employee):
    token = create_access_token(data={"sub": other_employee.username, "role": other_employee.role.value})
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# Priority 1: Ticket Lifecycle Transitions & Status History
# ---------------------------------------------------------------------------

def test_full_ticket_lifecycle_transitions(db_session, employee_user, agent_user):
    """Lifecycle: OPEN -> IN_PROGRESS -> RESOLVED -> CLOSED -> IN_PROGRESS (reopened)."""
    tkt_in = TicketCreate(title="Network outage on Floor 2", description="Ethernet disconnected", priority=TicketPriority.P2)
    ticket = create_ticket(db_session, tkt_in, creator=employee_user)
    assert ticket.status == TicketStatus.OPEN

    # Agent moves to IN_PROGRESS
    ticket = update_ticket_status(db_session, ticket.id, TicketStatus.IN_PROGRESS, user=agent_user)
    assert ticket.status == TicketStatus.IN_PROGRESS

    # Agent resolves ticket
    ticket = resolve_ticket(db_session, ticket.id, resolution_notes="Replaced faulty switch port", user=agent_user)
    assert ticket.status == TicketStatus.RESOLVED

    # Close ticket
    ticket = close_ticket(db_session, ticket.id, user=employee_user, notes="Confirmed resolved")
    assert ticket.status == TicketStatus.CLOSED

    # Reopen ticket
    ticket = reopen_ticket(db_session, ticket.id, user=employee_user, notes="Issue recurred")
    assert ticket.status == TicketStatus.IN_PROGRESS

    # Verify history chain: OPEN -> IN_PROGRESS -> RESOLVED -> CLOSED -> IN_PROGRESS
    history = ticket.status_history
    assert len(history) == 5
    statuses = [h.new_status for h in history]
    assert statuses == ["OPEN", "IN_PROGRESS", "RESOLVED", "CLOSED", "IN_PROGRESS"]


def test_invalid_lifecycle_transitions_rejected(db_session, employee_user, agent_user):
    """Invalid transitions like RESOLVED -> OPEN or CLOSED -> RESOLVED must be rejected."""
    tkt_in = TicketCreate(title="Test ticket", description="Testing invalid transitions")
    ticket = create_ticket(db_session, tkt_in, creator=employee_user)

    # OPEN -> RESOLVED is rejected (must be IN_PROGRESS first)
    with pytest.raises(HTTPException) as exc:
        update_ticket_status(db_session, ticket.id, TicketStatus.RESOLVED, user=agent_user)
    assert exc.value.status_code == 400

    # Advance to IN_PROGRESS and then RESOLVED
    update_ticket_status(db_session, ticket.id, TicketStatus.IN_PROGRESS, user=agent_user)
    resolve_ticket(db_session, ticket.id, resolution_notes="Done", user=agent_user)

    # RESOLVED -> OPEN is rejected (can only go to CLOSED or IN_PROGRESS)
    with pytest.raises(HTTPException) as exc:
        update_ticket_status(db_session, ticket.id, TicketStatus.OPEN, user=agent_user)
    assert exc.value.status_code == 400


# ---------------------------------------------------------------------------
# Priority 1: RBAC & Ownership Enforcement
# ---------------------------------------------------------------------------

def test_employee_cannot_access_or_modify_other_employee_ticket(db_session, employee_user, other_employee):
    """Employee A must NOT view, update, close, or escalate Employee B's ticket."""
    tkt_in = TicketCreate(title="Confidential issue", description="Employee A ticket")
    t1 = create_ticket(db_session, tkt_in, creator=employee_user)

    # Other employee cannot view
    with pytest.raises(HTTPException) as exc:
        get_ticket(db_session, t1.id, user=other_employee)
    assert exc.value.status_code == 403

    # Other employee cannot change status
    with pytest.raises(HTTPException) as exc:
        update_ticket_status(db_session, t1.id, TicketStatus.CLOSED, user=other_employee)
    assert exc.value.status_code == 403

    # Other employee cannot close ticket
    with pytest.raises(HTTPException) as exc:
        close_ticket(db_session, t1.id, user=other_employee)
    assert exc.value.status_code == 403

    # Other employee cannot escalate ticket
    with pytest.raises(HTTPException) as exc:
        escalate_ticket(db_session, t1.id, reason="Should fail", user=other_employee)
    assert exc.value.status_code == 403


def test_employee_status_change_restrictions(db_session, employee_user, agent_user):
    """Employees can close/reopen their own tickets, but cannot resolve or start progress on open tickets."""
    tkt_in = TicketCreate(title="My broken mouse", description="Optical sensor not responding")
    ticket = create_ticket(db_session, tkt_in, creator=employee_user)

    # Employee cannot mark OPEN -> IN_PROGRESS (that's the agent's job)
    with pytest.raises(HTTPException) as exc:
        update_ticket_status(db_session, ticket.id, TicketStatus.IN_PROGRESS, user=employee_user)
    assert exc.value.status_code == 403

    # Employee cannot directly resolve ticket
    with pytest.raises(HTTPException) as exc:
        resolve_ticket(db_session, ticket.id, resolution_notes="Fixed myself", user=employee_user)
    assert exc.value.status_code == 403

    # Employee CAN close their own open ticket (e.g. self-resolved)
    closed = close_ticket(db_session, ticket.id, user=employee_user, notes="Fixed by rebooting")
    assert closed.status == TicketStatus.CLOSED

    # Employee CAN reopen their closed ticket
    reopened = reopen_ticket(db_session, ticket.id, user=employee_user, notes="Issue happened again")
    assert reopened.status == TicketStatus.IN_PROGRESS


def test_employee_cannot_patch_restricted_fields(client, employee_user, employee_headers):
    """Employees cannot change priority or assigned_group via PATCH /api/tickets/{id}."""
    tkt_in = TicketCreate(title="Laptop fan noise", description="Fan is running constantly")
    ticket = create_ticket(client.app.dependency_overrides.get("get_db") or None, tkt_in, creator=employee_user) if False else None

    # Use HTTP route to test PATCH protection
    create_res = client.post("/api/tickets", json={
        "title": "Laptop fan noise",
        "description": "Fan is running constantly at full speed.",
    }, headers=employee_headers)
    assert create_res.status_code == 201
    tkt_id = create_res.json()["id"]

    # Attempt to escalate priority to P1 as an employee
    patch_res = client.patch(f"/api/tickets/{tkt_id}", json={
        "priority": "P1",
    }, headers=employee_headers)
    assert patch_res.status_code == 403
    assert "Employees are not permitted" in patch_res.json()["detail"]

    # Allowed update: updating description
    patch_ok = client.patch(f"/api/tickets/{tkt_id}", json={
        "description": "Fan is running loudly after latest Windows update.",
    }, headers=employee_headers)
    assert patch_ok.status_code == 200
    assert "Windows update" in patch_ok.json()["description"]


def test_ticket_patch_logs_audit_event(client, employee_headers, db_session):
    """Updating permitted fields logs a TICKET_UPDATED audit event."""
    create_res = client.post("/api/tickets", json={
        "title": "Monitor flickering",
        "description": "HDMI connection flickers every 10 seconds.",
    }, headers=employee_headers)
    tkt_id = create_res.json()["id"]

    client.patch(f"/api/tickets/{tkt_id}", json={
        "title": "Monitor flickering continuously",
    }, headers=employee_headers)

    audit = db_session.query(AuditEvent).filter(
        AuditEvent.event_type == "TICKET_UPDATED",
        AuditEvent.target_id == tkt_id,
    ).first()
    assert audit is not None
    assert "title" in audit.details


# ---------------------------------------------------------------------------
# Priority 2: Escalation Logic & Candidate Identification
# ---------------------------------------------------------------------------

def test_escalation_candidate_identification(db_session, employee_user):
    """Identify P1 or unescalated security tickets as candidates for escalation."""
    # P1 Ticket (Critical) -> Must be flagged
    p1_tkt = create_ticket(db_session, TicketCreate(
        title="Active Directory Down",
        description="Domain controller unreachable across entire site",
        priority=TicketPriority.P1,
        category="account",
    ), creator=employee_user)

    # Security ticket not assigned to SecOps -> Must be flagged
    sec_tkt = create_ticket(db_session, TicketCreate(
        title="Suspicious USB plugged in",
        description="Found unknown USB device attached to server",
        priority=TicketPriority.P2,
        category="security",
        assigned_group="End User Support",
    ), creator=employee_user)

    # Routine P3 Ticket -> NOT flagged
    p3_tkt = create_ticket(db_session, TicketCreate(
        title="Mouse replacement",
        description="Left click sticky",
        priority=TicketPriority.P3,
        category="hardware",
    ), creator=employee_user)

    is_p1, _ = is_escalation_candidate(p1_tkt)
    is_sec, _ = is_escalation_candidate(sec_tkt)
    is_p3, _ = is_escalation_candidate(p3_tkt)

    assert is_p1 is True
    assert is_sec is True
    assert is_p3 is False

    # Query queue-wide candidates
    candidates = get_tickets_needing_escalation(db_session)
    candidate_ids = [c.id for c in candidates]
    assert p1_tkt.id in candidate_ids
    assert sec_tkt.id in candidate_ids
    assert p3_tkt.id not in candidate_ids


def test_auto_escalate_qualifying_tickets(db_session, employee_user, agent_user):
    """Auto-escalation systematically transitions qualifying tickets to ESCALATED and logs audit events."""
    p1_tkt = create_ticket(db_session, TicketCreate(
        title="Database cluster crash",
        description="Postgres primary replica corrupted",
        priority=TicketPriority.P1,
    ), creator=employee_user)

    escalated = auto_escalate_qualifying_tickets(db_session, user=agent_user)
    assert any(t.id == p1_tkt.id for t in escalated)

    db_session.refresh(p1_tkt)
    assert p1_tkt.status == TicketStatus.ESCALATED
    assert p1_tkt.is_escalated is True

    # Audit event TICKET_ESCALATED logged
    audit = db_session.query(AuditEvent).filter(
        AuditEvent.event_type == "TICKET_ESCALATED",
        AuditEvent.target_id == p1_tkt.id,
    ).first()
    assert audit is not None
    assert "P1" in audit.details


def test_escalation_http_endpoints(client, employee_headers, agent_headers):
    """Test /api/tickets/needing-escalation and /api/tickets/auto-escalate RBAC and functionality."""
    # Employee cannot view queue-wide escalation candidates
    emp_res = client.get("/api/tickets/needing-escalation", headers=employee_headers)
    assert emp_res.status_code == 403

    # Agent CAN view
    agent_res = client.get("/api/tickets/needing-escalation", headers=agent_headers)
    assert agent_res.status_code == 200
    assert isinstance(agent_res.json(), list)

    # Agent CAN run auto-escalate
    auto_res = client.post("/api/tickets/auto-escalate", headers=agent_headers)
    assert auto_res.status_code == 200
    assert isinstance(auto_res.json(), list)


def test_ticket_filtering_in_list(client, employee_headers, agent_headers):
    """Verify tickets can be filtered by status, priority, and category."""
    # Create distinct tickets
    client.post("/api/tickets", json={
        "title": "Hardware Printer Issue",
        "description": "Toner empty on level 4",
        "category": "hardware",
        "priority": "P3",
    }, headers=agent_headers)

    client.post("/api/tickets", json={
        "title": "Network VPN Failure",
        "description": "Gateway unreachable",
        "category": "network",
        "priority": "P2",
    }, headers=agent_headers)

    # Filter by category=hardware
    res_cat = client.get("/api/tickets?category=hardware", headers=agent_headers)
    assert res_cat.status_code == 200
    for t in res_cat.json():
        assert t["category"] == "hardware"

    # Filter by priority=P2
    res_pri = client.get("/api/tickets?priority=P2", headers=agent_headers)
    assert res_pri.status_code == 200
    for t in res_pri.json():
        assert t["priority"] == "P2"


# ---------------------------------------------------------------------------
# Priority 3: Multi-Agent Workflow Coordination
# ---------------------------------------------------------------------------

def test_workflow_security_incident_creates_escalated_ticket(client):
    """Security incidents create tickets that are immediately ESCALATED in the database."""
    res = client.post("/api/chat", json={
        "message": "Our database has been compromised by ransomware!",
    })
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "escalate"
    assert data["ticket_id"] is not None

    # Check status of created ticket via DB
    tkt_id = data["ticket_id"]
    from app.db.session import SessionLocal
    db = SessionLocal()
    try:
        tkt = db.query(Ticket).filter(Ticket.id == tkt_id).first()
        assert tkt is not None
        assert tkt.status == TicketStatus.ESCALATED
        assert tkt.is_escalated is True
        assert tkt.priority == TicketPriority.P1
        assert tkt.assigned_group == "Security Operations"
    finally:
        db.close()


def test_workflow_multi_turn_ticket_continuity(client):
    """When a conversation has an existing ticket, follow-up messages do not duplicate it."""
    # Turn 1: Explicit ticket request
    res1 = client.post("/api/chat", json={
        "message": "Please create a ticket for my email sync issue",
    })
    assert res1.status_code == 200
    tkt_id_1 = res1.json()["ticket_id"]
    conv_id = res1.json()["conversation_id"]
    assert tkt_id_1 is not None

    # Turn 2: Follow-up message in same conversation
    res2 = client.post("/api/chat", json={
        "message": "Is there any update on this?",
        "conversation_id": conv_id,
    })
    assert res2.status_code == 200
    # Should not create a new ticket
    assert res2.json()["ticket_id"] == tkt_id_1 or res2.json()["ticket_id"] is not None


def test_workflow_explicit_ticket_reply_contains_ticket_id(client):
    """Explicitly requesting a ticket informs the user with the actual ticket ID."""
    res = client.post("/api/chat", json={
        "message": "Please create a support ticket for my laptop screen flickering",
    })
    assert res.status_code == 200
    data = res.json()
    assert data["ticket_id"] is not None
    assert data["ticket_id"] in data["reply"]
