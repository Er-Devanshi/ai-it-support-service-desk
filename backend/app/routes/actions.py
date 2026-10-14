"""
Controlled IT Actions and Simulated Execution routes for ServiceDesk-AI.
Exposes allowlist and safe simulated workflows.
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.models.orm import User
from app.services.actions.action_registry import (
    ACTION_REGISTRY,
    ActionDefinition,
    ActionResult,
    get_action_definition,
    execute_action,
)
from app.services.auth_service import get_current_user_optional

router = APIRouter(prefix="/actions", tags=["Actions"])


class ActionExecuteRequest(BaseModel):
    params: Dict[str, Any] = {}


@router.get("", response_model=List[ActionDefinition])
def list_actions():
    """List all permitted simulated IT actions in the system allowlist."""
    return [entry[0] for entry in ACTION_REGISTRY.values()]


@router.post("/{action_name}/execute", response_model=ActionResult)
def execute_permitted_action(
    action_name: str,
    req: ActionExecuteRequest,
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """
    Execute a low-risk permitted simulated IT action.
    High-risk actions requiring approval are blocked from direct invocation.
    """
    action_def = get_action_definition(action_name)
    if not action_def:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Action '{action_name}' is not in the allowed registry.",
        )

    if action_def.requires_approval:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Action '{action_name}' is protected and requires human approval before execution. Submit an approval request.",
        )

    return execute_action(action_name, req.params, user=current_user)
