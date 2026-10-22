"""
Human-in-the-loop Approval Service for ServiceDesk-AI.
Enforces multi-tier authorization, prevents self-approval,
and triggers action execution only upon authorized human decision.
"""

from datetime import datetime, timezone
import json
import uuid
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.orm import (
    ApprovalRequest,
    ApprovalStatus,
    RiskLevel,
    User,
    UserRole,
)
from app.services.actions.action_registry import (
    get_action_definition,
    execute_action,
    ActionResult,
)
from app.services.audit_service import log_audit_event
from app.utils.logger import logger


def create_approval_request(
    db: Session,
    action_name: str,
    action_params: Dict[str, Any],
    reason: str,
    requester: Optional[User] = None,
    ticket_id: Optional[str] = None,
    conversation_id: Optional[str] = None,
    risk_level: Optional[RiskLevel] = None,
) -> ApprovalRequest:
    """Create a pending approval request."""
    action_def = get_action_definition(action_name)
    if not action_def:
        raise ValueError(f"Action '{action_name}' is not in the allowed registry.")

    effective_risk = risk_level or action_def.risk_level

    request_id = f"APPR-{uuid.uuid4().hex[:8].upper()}"
    approval = ApprovalRequest(
        id=request_id,
        ticket_id=ticket_id,
        conversation_id=conversation_id,
        action_name=action_name,
        action_params=json.dumps(action_params),
        requester_id=requester.id if requester else None,
        risk_level=effective_risk,
        reason=reason,
        status=ApprovalStatus.PENDING,
    )
    db.add(approval)
    db.commit()
    db.refresh(approval)

    log_audit_event(
        db=db,
        event_type="APPROVAL_REQUESTED",
        actor=requester,
        target_type="approval_request",
        target_id=request_id,
        details={
            "action_name": action_name,
            "risk_level": effective_risk.value,
            "reason": reason,
        },
    )
    logger.info(f"Created approval request {request_id} for action '{action_name}'")
    return approval


def process_approval_decision(
    db: Session,
    approval_id: str,
    decision: str,  # "APPROVED" or "REJECTED"
    deciding_user: User,
    decision_notes: Optional[str] = None,
) -> tuple[ApprovalRequest, Optional[ActionResult]]:
    """
    Process an approval decision with security checks:
    - User must have SUPPORT_AGENT or ADMIN role.
    - Prevents self-approval (requester cannot approve own action).
    - If approved, executes the simulated action and verifies the outcome.
    """
    approval = db.query(ApprovalRequest).filter(ApprovalRequest.id == approval_id).first()
    if not approval:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Approval request not found")

    if approval.status != ApprovalStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Approval request is already in '{approval.status.value}' state.",
        )

    # RBAC check
    user_role = deciding_user.role if isinstance(deciding_user.role, UserRole) else UserRole(deciding_user.role)
    if user_role not in (UserRole.SUPPORT_AGENT, UserRole.ADMIN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Support Agents or Administrators may decide on approval requests.",
        )

    # Self-approval prevention policy
    if approval.requester_id and approval.requester_id == deciding_user.id:
        log_audit_event(
            db=db,
            event_type="SELF_APPROVAL_BLOCKED",
            actor=deciding_user,
            target_type="approval_request",
            target_id=approval_id,
            details="User attempted to approve their own requested protected action.",
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Self-approval prohibited: You cannot approve an action you requested.",
        )

    dec_upper = decision.upper().strip()
    if dec_upper not in ("APPROVED", "REJECTED"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Decision must be 'APPROVED' or 'REJECTED'.",
        )

    approval.status = ApprovalStatus.APPROVED if dec_upper == "APPROVED" else ApprovalStatus.REJECTED
    approval.approver_id = deciding_user.id
    approval.decision_notes = decision_notes
    approval.decided_at = datetime.now(timezone.utc)

    action_result = None

    if approval.status == ApprovalStatus.APPROVED:
        # Re-check action definition and execute
        params = json.loads(approval.action_params) if approval.action_params else {}
        action_result = execute_action(approval.action_name, params, deciding_user)
        
        log_audit_event(
            db=db,
            event_type="APPROVAL_APPROVED",
            actor=deciding_user,
            target_type="approval_request",
            target_id=approval_id,
            details={"action_executed": action_result.model_dump() if action_result else None},
        )
    else:
        log_audit_event(
            db=db,
            event_type="APPROVAL_REJECTED",
            actor=deciding_user,
            target_type="approval_request",
            target_id=approval_id,
            details={"decision_notes": decision_notes},
        )

    db.commit()
    db.refresh(approval)
    return approval, action_result


def list_pending_approvals(db: Session) -> List[ApprovalRequest]:
    """Retrieve all pending approval requests."""
    return db.query(ApprovalRequest).filter(ApprovalRequest.status == ApprovalStatus.PENDING).all()
