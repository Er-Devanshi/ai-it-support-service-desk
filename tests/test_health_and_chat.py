"""
Tests for Health and Chat endpoints.
Verifies backward compatibility with Phase 1 and input validation rules.
"""

import pytest


def test_health_check_endpoint(client):
    """Test 1: Health endpoint returns correct status, service, and phase."""
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "running"
    assert data["service"] == "ServiceDesk-AI"
    assert "phase" in data
    assert "llm_provider" in data


@pytest.mark.parametrize(
    "msg, exp_cat, exp_status",
    [
        ("My Wi-Fi is not working", "network", "answered"),
        ("I need to reset my password", "account", "answered"),
        ("VPN is not connecting", "network", "answered"),
        ("My email is not syncing", "email", "answered"),
        ("The printer is not responding", "hardware", "answered"),
        ("I need to install software", "software", "answered"),
        ("My account is locked", "account", "answered"),
        ("My computer is very slow", "performance", "answered"),
        ("MFA authenticator not working", "security", "answered"),
        ("I have no internet connectivity", "network", "answered"),
        ("Something very unusual happened", "unknown", "escalate"),
    ],
)
def test_phase1_chat_compatibility(client, msg, exp_cat, exp_status):
    """Test 2: Exact Phase 1 verification test cases continue to match."""
    res = client.post("/api/chat", json={"message": msg})
    assert res.status_code == 200
    data = res.json()
    assert data["category"] == exp_cat, f"For '{msg}', expected category {exp_cat}, got {data['category']}"
    assert data["status"] == exp_status, f"For '{msg}', expected status {exp_status}, got {data['status']}"
    assert "reply" in data and len(data["reply"]) > 10
    assert "note" in data


def test_chat_input_validation(client):
    """Test 3: Chat input validation rejects empty and oversized messages."""
    # Empty message
    res_empty = client.post("/api/chat", json={"message": ""})
    assert res_empty.status_code == 422

    # Missing message field
    res_missing = client.post("/api/chat", json={})
    assert res_missing.status_code == 422

    # Oversized message (> 2000 chars)
    oversized = "A" * 2500
    res_oversized = client.post("/api/chat", json={"message": oversized})
    assert res_oversized.status_code == 422
