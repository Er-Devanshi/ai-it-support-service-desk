"""
Audit logging service for security and compliance tracking.
Records events persistently into SQLite/SQLAlchemy.
"""

from typing import Optional, Any
import json
from sqlalchemy.orm import Session
from app.models.orm import AuditEvent, User
from app.utils.logger import logger


def log_audit_event(
    db: Session,
    event_type: str,
    actor: Optional[User] = None,
    actor_id: Optional[int] = None,
    actor_username: Optional[str] = None,
    target_type: Optional[str] = None,
    target_id: Optional[str] = None,
    details: Optional[Any] = None,
    ip_address: Optional[str] = None,
) -> AuditEvent:
    """Record an audit event."""
    if actor:
        actor_id = actor.id
        actor_username = actor.username

    details_str = None
    if details is not None:
        if isinstance(details, (dict, list)):
            details_str = json.dumps(details)
        else:
            details_str = str(details)

    event = AuditEvent(
        event_type=event_type,
        actor_id=actor_id,
        actor_username=actor_username,
        target_type=target_type,
        target_id=str(target_id) if target_id else None,
        details=details_str,
        ip_address=ip_address,
    )
    db.add(event)
    try:
        db.commit()
        db.refresh(event)
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to record audit event '{event_type}': {e}")
    return event
