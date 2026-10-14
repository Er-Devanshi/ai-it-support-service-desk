"""
Human-in-the-loop Approval routes for ServiceDesk-AI.
Allows authorized agents/admins to review and decide on protected action requests.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.orm import User, UserRole, ApprovalRequest
from app.models.ticket_schemas import (
    ApprovalRequestOut,
    ApprovalDecisionRequest,
)
from app.services.auth_service import get_current_user, require_roles
from app.services.approval_service import (
    list_pending_approvals,
    process_approval_decision,
)

router = APIRouter(prefix="/approvals", tags=["Approvals"])


@router.get("", response_model=List[ApprovalRequestOut])
def get_approvals(
    status_filter: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.SUPPORT_AGENT, UserRole.ADMIN])),
):
    """List pending approval requests (Support Agent or Admin only)."""
    query = db.query(ApprovalRequest)
    if status_filter:
        query = query.filter(ApprovalRequest.status == status_filter.upper())
    else:
        query = query.filter(ApprovalRequest.status == "PENDING")
    return query.order_by(ApprovalRequest.created_at.desc()).all()


@router.post("/{approval_id}/decision", response_model=ApprovalRequestOut)
def decide_approval(
    approval_id: str,
    decision_in: ApprovalDecisionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.SUPPORT_AGENT, UserRole.ADMIN])),
):
    """Approve or reject a pending request. Prevents self-approval."""
    approval, action_result = process_approval_decision(
        db=db,
        approval_id=approval_id,
        decision=decision_in.decision,
        deciding_user=current_user,
        decision_notes=decision_in.decision_notes,
    )
    return approval
