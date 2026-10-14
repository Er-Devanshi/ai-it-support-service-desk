"""
Audit event log routes for ServiceDesk-AI.
Restricted to Administrators.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.orm import User, UserRole, AuditEvent
from app.models.ticket_schemas import AuditEventOut
from app.services.auth_service import require_roles

router = APIRouter(prefix="/audit", tags=["Audit"])


@router.get("", response_model=List[AuditEventOut])
def get_audit_logs(
    skip: int = 0,
    limit: int = 100,
    event_type: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN])),
):
    """Retrieve audit log records (Administrator only)."""
    query = db.query(AuditEvent)
    if event_type:
        query = query.filter(AuditEvent.event_type == event_type)
    return query.order_by(AuditEvent.timestamp.desc()).offset(skip).limit(limit).all()
