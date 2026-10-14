"""
Tests for JWT Authentication, Password Hashing, and Role-Based Access Control (RBAC).
"""

import pytest


def test_user_registration_and_login(client):
    """Test 12: Register new user, login, and verify returned JWT token."""
    reg_res = client.post(
        "/api/auth/register",
        json={"username": "newuser", "email": "new@company.com", "password": "SecurePassword123!"},
    )
    assert reg_res.status_code == 201
    assert reg_res.json()["username"] == "newuser"

    # Login
    login_res = client.post(
        "/api/auth/login",
        json={"username": "newuser", "password": "SecurePassword123!"},
    )
    assert login_res.status_code == 200
    token_data = login_res.json()
    assert "access_token" in token_data
    assert token_data["token_type"] == "bearer"

    # Profile fetch with token
    headers = {"Authorization": f"Bearer {token_data['access_token']}"}
    me_res = client.get("/api/auth/me", headers=headers)
    assert me_res.status_code == 200
    assert me_res.json()["username"] == "newuser"


def test_invalid_credentials_rejected(client):
    """Test 12b: Wrong password receives 401 Unauthorized."""
    res = client.post(
        "/api/auth/login",
        json={"username": "test_employee", "password": "WrongPassword"},
    )
    assert res.status_code == 401
    assert "Incorrect username or password" in res.json()["detail"]


def test_rbac_admin_audit_restriction(client, employee_headers, admin_headers):
    """Test 13: Non-admins receive 403 Forbidden when accessing audit logs."""
    # Employee blocked
    res_emp = client.get("/api/audit", headers=employee_headers)
    assert res_emp.status_code == 403

    # Admin allowed
    res_adm = client.get("/api/audit", headers=admin_headers)
    assert res_adm.status_code == 200
    assert isinstance(res_adm.json(), list)
