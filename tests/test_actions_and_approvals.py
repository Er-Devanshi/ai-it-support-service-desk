"""
Tests for Controlled IT Actions, Human Approvals, Self-Approval Prevention, and Audit Events.
"""

import pytest
from fastapi import HTTPException
from app.services.actions.action_registry import execute_action, get_action_definition
from app.services.approval_service import (
    create_approval_request,
    process_approval_decision,
    list_pending_approvals,
)
from app.models.orm import ApprovalStatus, AuditEvent


def test_action_allowlist_enforcement():
    """Test 18: Unlisted/arbitrary actions are rejected; allowlisted simulated actions execute."""
    # Arbitrary action
    bad_res = execute_action("delete_root_directory", {})
    assert bad_res.success is False
    assert "not in the permitted" in bad_res.message

    # Allowlisted low-risk action
    good_res = execute_action("check_service_health", {"service_name": "vpn"})
    assert good_res.success is True
    assert good_res.is_simulation is True
    assert "OPERATIONAL" in good_res.message


def test_approval_workflow_lifecycle(db_session, employee_user, agent_user):
    """Test 19: Protected action generates approval request and executes only upon authorized approval."""
    approval = create_approval_request(
        db=db_session,
        action_name="unlock_account",
        action_params={"username": "john.doe"},
        reason="User locked out after 3 password attempts.",
        requester=employee_user,
    )
    assert approval.id.startswith("APPR-")
    assert approval.status == ApprovalStatus.PENDING

    # Agent approves request
    decided, action_res = process_approval_decision(
        db=db_session,
        approval_id=approval.id,
        decision="APPROVED",
        deciding_user=agent_user,
        decision_notes="Identity verified via phone call.",
    )
    assert decided.status == ApprovalStatus.APPROVED
    assert action_res is not None
    assert action_res.success is True
    assert "Successfully unlocked account" in action_res.message


def test_self_approval_prevention(db_session, agent_user):
    """Test 20a: A user cannot approve their own requested protected action."""
    approval = create_approval_request(
        db=db_session,
        action_name="unlock_account",
        action_params={"username": "agent_self"},
        reason="Testing self approval",
        requester=agent_user,
    )

    # Attempting to approve own action
    with pytest.raises(HTTPException) as exc_info:
        process_approval_decision(
            db=db_session,
            approval_id=approval.id,
            decision="APPROVED",
            deciding_user=agent_user,
        )
    assert exc_info.value.status_code == 403
    assert "Self-approval prohibited" in exc_info.value.detail


def test_rejected_action_prevention(db_session, employee_user, agent_user):
    """Test 20b: Rejected approval requests cannot execute action."""
    approval = create_approval_request(
        db=db_session,
        action_name="grant_resource_access",
        action_params={"username": "employee", "resource": "Restricted-DB"},
        reason="Access to sensitive DB",
        requester=employee_user,
    )

    # Agent rejects
    decided, action_res = process_approval_decision(
        db=db_session,
        approval_id=approval.id,
        decision="REJECTED",
        deciding_user=agent_user,
        decision_notes="Manager approval missing.",
    )
    assert decided.status == ApprovalStatus.REJECTED
    assert action_res is None  # Action was NOT executed


def test_audit_event_logged(db_session, employee_user):
    """Test 21: Enterprise events create persistent audit log entries."""
    from app.services.audit_service import log_audit_event

    log_audit_event(
        db=db_session,
        event_type="TEST_SECURITY_EVENT",
        actor=employee_user,
        target_type="system",
        target_id="node-1",
        details="Suspicious login pattern detected",
    )

    audit_entry = db_session.query(AuditEvent).filter(AuditEvent.event_type == "TEST_SECURITY_EVENT").first()
    assert audit_entry is not None
    assert audit_entry.actor_username == employee_user.username
    assert "Suspicious login pattern" in audit_entry.details
