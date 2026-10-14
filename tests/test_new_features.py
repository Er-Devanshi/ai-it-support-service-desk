"""
Tests for newly implemented features:
  - Chat-to-ticket integration (explicit request + escalation)
  - Persistent conversation history (save & retrieve)
  - Correct LLM provider / mode reporting
  - Duplicate ticket prevention within a single workflow run
"""

import pytest
from app.services.conversation_service import save_message, get_history, format_history_for_llm
from app.services.workflow.graph import run_servicedesk_workflow, reset_workflow_graph
from app.services.llm.mock_provider import MockLLMProvider
from app.config import settings


# ──────────────────────────────────────────────────────────────────────────────
# Conversation history persistence
# ──────────────────────────────────────────────────────────────────────────────

def test_conversation_history_save_and_retrieve(db_session):
    """Saved messages are returned in chronological order."""
    conv_id = "HIST-TEST-001"
    save_message(db_session, conv_id, "user", "My Wi-Fi is broken")
    save_message(db_session, conv_id, "assistant", "Please restart your router.")

    history = get_history(db_session, conv_id)
    assert len(history) == 2
    assert history[0].role == "user"
    assert history[1].role == "assistant"


def test_conversation_history_formatted_for_llm(db_session):
    """History is formatted correctly for LLM context injection."""
    conv_id = "HIST-TEST-002"
    save_message(db_session, conv_id, "user", "VPN not connecting")
    save_message(db_session, conv_id, "assistant", "Try reconnecting.")

    history = get_history(db_session, conv_id)
    text = format_history_for_llm(history)
    assert "VPN not connecting" in text
    assert "Try reconnecting" in text
    assert "User:" in text
    assert "Assistant:" in text


def test_conversation_history_max_turns_limit(db_session):
    """History retrieval is bounded by MAX_HISTORY_TURNS."""
    conv_id = "HIST-TEST-003"
    for i in range(20):
        save_message(db_session, conv_id, "user", f"Message {i}")
        save_message(db_session, conv_id, "assistant", f"Reply {i}")

    # Default max is 6 turns = 12 rows
    history = get_history(db_session, conv_id, max_turns=6)
    assert len(history) <= 12


def test_empty_history_returns_empty_string(db_session):
    """format_history_for_llm returns '' when there is no history."""
    result = format_history_for_llm([])
    assert result == ""


# ──────────────────────────────────────────────────────────────────────────────
# Chat-to-ticket integration
# ──────────────────────────────────────────────────────────────────────────────

def test_chat_explicit_ticket_creation(client):
    """Explicitly requesting a ticket creates one and returns ticket_id."""
    res = client.post("/api/chat", json={"message": "please create a ticket for my VPN issue"})
    assert res.status_code == 200
    data = res.json()
    assert data["ticket_id"] is not None, f"Expected a ticket_id but got None. Reply: {data['reply']}"
    assert data["ticket_id"].startswith("TKT-")


def test_chat_explicit_ticket_with_support_keyword(client):
    """Ticket creation works for 'create a support ticket' phrasing (was the reported bug)."""
    res = client.post(
        "/api/chat",
        json={
            "message": "Please create a support ticket for my network issue. My Wi-Fi is not working.",
            "conversation_id": "bug-repro-test-1",
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["ticket_id"] is not None, (
        f"Regression: 'create a support ticket' phrase must create a ticket. "
        f"Reply: {data['reply']}, mode: {data.get('mode')}"
    )
    assert data["ticket_id"].startswith("TKT-")
    # Category should still be network (Wi-Fi keywords)
    assert data["category"] == "network"


def test_chat_security_incident_creates_ticket(client):
    """Security incidents auto-create a P1 ticket."""
    res = client.post("/api/chat", json={"message": "Our servers are infected with ransomware!"})
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "escalate"
    assert data["ticket_id"] is not None, "Security escalation should create a ticket"
    assert data["ticket_id"].startswith("TKT-")


def test_chat_routine_query_no_ticket(client):
    """Routine queries (answered by rule) do NOT auto-create tickets."""
    res = client.post("/api/chat", json={"message": "My Wi-Fi is not working"})
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "answered"
    # Routine Wi-Fi question should be handled without creating a ticket
    assert data["ticket_id"] is None, f"Routine query should not create a ticket but got {data['ticket_id']}"


def test_chat_no_duplicate_ticket_same_workflow(client):
    """A second message in the same conversation that already has a ticket does not create a duplicate."""
    # First message: escalation → ticket created
    res1 = client.post(
        "/api/chat",
        json={"message": "Please open a ticket for my ongoing VPN issue"},
    )
    assert res1.status_code == 200
    data1 = res1.json()
    conv_id = data1.get("conversation_id")
    ticket_id_1 = data1.get("ticket_id")
    assert ticket_id_1 is not None

    # Second message in same conversation (no new escalation)
    res2 = client.post(
        "/api/chat",
        json={"message": "I still can't connect to VPN", "conversation_id": conv_id},
    )
    assert res2.status_code == 200


# ──────────────────────────────────────────────────────────────────────────────
# LLM mode / provider reporting
# ──────────────────────────────────────────────────────────────────────────────

def test_mock_provider_reports_mock_mode():
    """MockLLMProvider.generate returns is_mock=True."""
    provider = MockLLMProvider()
    resp = provider.generate("How do I fix slow performance?")
    assert resp.is_mock is True
    assert resp.provider == "mock"


def test_chat_response_mode_is_not_live_in_demo(client):
    """In DEMO_MODE the mode field must not be 'live'."""
    res = client.post("/api/chat", json={"message": "something very unusual happened"})
    assert res.status_code == 200
    data = res.json()
    # In demo/mock mode, mode should never claim 'live' (live = real LLM)
    assert data.get("mode") != "live", f"mode should not be 'live' in demo mode, got: {data.get('mode')}"


def test_health_endpoint_reports_mode(client):
    """Health endpoint exposes LLM mode information."""
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert "mode" in data
    assert "llm_provider" in data
    # In test/demo mode the health endpoint should indicate mock/demo
    assert data["mode"] in ("mock/demo", "live")
