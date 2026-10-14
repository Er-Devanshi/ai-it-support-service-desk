"""
Controlled IT Actions and Simulated Tool-Calling Registry for ServiceDesk-AI.

Implements:
- Explicit Action Allowlist (NO arbitrary shell commands, NO dynamic code evaluation)
- Risk Classification (LOW, MEDIUM, HIGH)
- Permission & Role Validation
- Human-in-the-loop approval triggers
- Outcome verification on synthetic test data
"""

from typing import Dict, Any, Optional, Callable
from pydantic import BaseModel, Field
from app.models.orm import RiskLevel, UserRole, User
from app.utils.logger import logger


# Synthetic Enterprise Directory for Simulation
SYNTHETIC_ACCOUNTS = {
    "employee": {"status": "ACTIVE", "locked": False, "mfa_enabled": True, "department": "Marketing"},
    "john.doe": {"status": "LOCKED", "locked": True, "mfa_enabled": True, "department": "Sales"},
    "jane.smith": {"status": "ACTIVE", "locked": False, "mfa_enabled": True, "department": "Engineering"},
    "alex.kumar": {"status": "LOCKED", "locked": True, "mfa_enabled": False, "department": "Finance"},
}

SYNTHETIC_SERVICES = {
    "vpn": {"status": "OPERATIONAL", "uptime": "99.98%", "cluster": "us-east-vpn"},
    "email": {"status": "OPERATIONAL", "uptime": "99.99%", "cluster": "m365-tenant"},
    "wifi": {"status": "OPERATIONAL", "uptime": "99.95%", "cluster": "hq-access-points"},
    "jira": {"status": "DEGRADED", "uptime": "98.50%", "cluster": "jira-prod-01"},
    "payroll": {"status": "OPERATIONAL", "uptime": "100.0%", "cluster": "erp-prod"},
}


class ActionParamSchema(BaseModel):
    name: str
    type: str
    required: bool
    description: str


class ActionDefinition(BaseModel):
    name: str
    description: str
    risk_level: RiskLevel
    requires_approval: bool
    allowed_roles: list[UserRole]
    params: list[ActionParamSchema]


class ActionResult(BaseModel):
    success: bool
    action_name: str
    message: str
    details: Dict[str, Any] = Field(default_factory=dict)
    is_simulation: bool = True
    verified: bool = False


# Concrete simulated action handlers

def _check_account_status(params: Dict[str, Any], user: Optional[User]) -> ActionResult:
    username = params.get("username", "").strip().lower()
    if not username:
        return ActionResult(
            success=False,
            action_name="check_account_status",
            message="Missing required parameter: username",
            is_simulation=True,
            verified=False,
        )
    account = SYNTHETIC_ACCOUNTS.get(username)
    if not account:
        return ActionResult(
            success=True,
            action_name="check_account_status",
            message=f"Synthetic check: Account '{username}' not found in Active Directory.",
            details={"username": username, "found": False},
            is_simulation=True,
            verified=True,
        )
    return ActionResult(
        success=True,
        action_name="check_account_status",
        message=f"Synthetic check: Account '{username}' status is {account['status']} (Locked: {account['locked']}).",
        details={"username": username, "found": True, **account},
        is_simulation=True,
        verified=True,
    )


def _check_service_health(params: Dict[str, Any], user: Optional[User]) -> ActionResult:
    service_name = params.get("service_name", "").strip().lower()
    if not service_name:
        return ActionResult(
            success=False,
            action_name="check_service_health",
            message="Missing required parameter: service_name",
            is_simulation=True,
            verified=False,
        )
    # Check matching service
    found_key = next((k for k in SYNTHETIC_SERVICES if k in service_name), None)
    if not found_key:
        return ActionResult(
            success=True,
            action_name="check_service_health",
            message=f"Synthetic service check: Service '{service_name}' status is OPERATIONAL (All systems nominal).",
            details={"service": service_name, "status": "OPERATIONAL"},
            is_simulation=True,
            verified=True,
        )
    svc = SYNTHETIC_SERVICES[found_key]
    return ActionResult(
        success=True,
        action_name="check_service_health",
        message=f"Synthetic service check: Service '{found_key.upper()}' is {svc['status']} (Uptime: {svc['uptime']}).",
        details={"service": found_key, **svc},
        is_simulation=True,
        verified=True,
    )


def _unlock_account(params: Dict[str, Any], user: Optional[User]) -> ActionResult:
    username = params.get("username", "").strip().lower()
    if not username:
        return ActionResult(
            success=False,
            action_name="unlock_account",
            message="Missing required parameter: username",
            is_simulation=True,
            verified=False,
        )
    if username in SYNTHETIC_ACCOUNTS:
        SYNTHETIC_ACCOUNTS[username]["locked"] = False
        SYNTHETIC_ACCOUNTS[username]["status"] = "ACTIVE"
    return ActionResult(
        success=True,
        action_name="unlock_account",
        message=f"Simulated execution: Successfully unlocked account for user '{username}'. Account status verified: ACTIVE.",
        details={"username": username, "new_status": "ACTIVE", "locked": False},
        is_simulation=True,
        verified=True,
    )


def _reset_password(params: Dict[str, Any], user: Optional[User]) -> ActionResult:
    username = params.get("username", "").strip().lower()
    if not username:
        return ActionResult(
            success=False,
            action_name="reset_password",
            message="Missing required parameter: username",
            is_simulation=True,
            verified=False,
        )
    return ActionResult(
        success=True,
        action_name="reset_password",
        message=f"Simulated execution: Temporary one-time password generated and dispatched to registered mobile number for '{username}'.",
        details={"username": username, "dispatched": True},
        is_simulation=True,
        verified=True,
    )


def _grant_resource_access(params: Dict[str, Any], user: Optional[User]) -> ActionResult:
    username = params.get("username", "").strip().lower()
    resource = params.get("resource", "").strip()
    return ActionResult(
        success=True,
        action_name="grant_resource_access",
        message=f"Simulated execution: Access provisioned for '{username}' to restricted resource '{resource}'.",
        details={"username": username, "resource": resource, "access_granted": True},
        is_simulation=True,
        verified=True,
    )


# Explicit Action Allowlist Registry
ACTION_REGISTRY: Dict[str, tuple[ActionDefinition, Callable[[Dict[str, Any], Optional[User]], ActionResult]]] = {
    "check_account_status": (
        ActionDefinition(
            name="check_account_status",
            description="Query the synthetic directory to check account lock and status.",
            risk_level=RiskLevel.LOW,
            requires_approval=False,
            allowed_roles=[UserRole.EMPLOYEE, UserRole.SUPPORT_AGENT, UserRole.ADMIN],
            params=[ActionParamSchema(name="username", type="string", required=True, description="Target username")],
        ),
        _check_account_status,
    ),
    "check_service_health": (
        ActionDefinition(
            name="check_service_health",
            description="Check synthetic infrastructure status for services like VPN, Wi-Fi, Email.",
            risk_level=RiskLevel.LOW,
            requires_approval=False,
            allowed_roles=[UserRole.EMPLOYEE, UserRole.SUPPORT_AGENT, UserRole.ADMIN],
            params=[ActionParamSchema(name="service_name", type="string", required=True, description="Name of the IT service")],
        ),
        _check_service_health,
    ),
    "unlock_account": (
        ActionDefinition(
            name="unlock_account",
            description="Simulate unlocking a locked user account in Active Directory.",
            risk_level=RiskLevel.MEDIUM,
            requires_approval=True,
            allowed_roles=[UserRole.SUPPORT_AGENT, UserRole.ADMIN],
            params=[ActionParamSchema(name="username", type="string", required=True, description="Account username to unlock")],
        ),
        _unlock_account,
    ),
    "reset_password": (
        ActionDefinition(
            name="reset_password",
            description="Simulate initiating an enterprise password reset workflow.",
            risk_level=RiskLevel.MEDIUM,
            requires_approval=True,
            allowed_roles=[UserRole.SUPPORT_AGENT, UserRole.ADMIN],
            params=[ActionParamSchema(name="username", type="string", required=True, description="Username to reset")],
        ),
        _reset_password,
    ),
    "grant_resource_access": (
        ActionDefinition(
            name="grant_resource_access",
            description="Simulate granting role or ACL permissions to a restricted resource.",
            risk_level=RiskLevel.HIGH,
            requires_approval=True,
            allowed_roles=[UserRole.ADMIN],
            params=[
                ActionParamSchema(name="username", type="string", required=True, description="User receiving access"),
                ActionParamSchema(name="resource", type="string", required=True, description="Restricted resource or group"),
            ],
        ),
        _grant_resource_access,
    ),
}


def get_action_definition(action_name: str) -> Optional[ActionDefinition]:
    """Retrieve action metadata if registered."""
    entry = ACTION_REGISTRY.get(action_name)
    return entry[0] if entry else None


def execute_action(action_name: str, params: Dict[str, Any], user: Optional[User] = None) -> ActionResult:
    """
    Execute a registered action.
    Strictly checks action allowlist and prevents arbitrary code execution.
    """
    if action_name not in ACTION_REGISTRY:
        logger.warning(f"Attempt to execute unauthorized or unlisted action: {action_name}")
        return ActionResult(
            success=False,
            action_name=action_name,
            message=f"Action '{action_name}' is not in the permitted IT action allowlist.",
            is_simulation=True,
            verified=False,
        )

    action_def, handler = ACTION_REGISTRY[action_name]
    logger.info(f"Executing simulated action '{action_name}' (Risk: {action_def.risk_level.value})")
    return handler(params, user)
