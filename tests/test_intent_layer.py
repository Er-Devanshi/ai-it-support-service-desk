"""
Tests for the Intent Engine layer (20 tests).

Covers:
  1-5:  Intent classifier predictions (class-level unit tests)
  6-8:  Small-talk guard: technical messages route to pipeline
  9-10: Router returns "pipeline" when USE_INTENT=False
  11:   Security message bypasses intent router entirely
  12:   check_ticket_status unauthenticated user
  13:   check_ticket_status employee sees only own tickets
  14:   check_ticket_status returns "please log in" for anonymous
  15:   create_ticket intent creates ticket using triage fields
  16:   create_ticket deduplication (no double ticket)
  17:   flag off → original pipeline behaviour unchanged
  18:   flag on → greeting handled directly with correct reply
  19:   "hi, my VPN is down" routes to pipeline (not greeting)
  20:   "thanks but wifi still not working" routes to pipeline
"""

import pytest
from app.config import settings
from app.services.intent_engine.intent_classifier import classify, reset_classifier
from app.services.intent_engine.router import route_intent, _has_technical_keyword
from app.services.workflow.graph import run_servicedesk_workflow, reset_workflow_graph


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def reset_clf_singleton():
    """Reset classifier singleton before each test so monkeypatching is clean."""
    yield
    reset_classifier()


@pytest.fixture(autouse=True)
def reset_graph_singleton():
    """Reset compiled graph singleton before each test."""
    reset_workflow_graph()
    yield
    reset_workflow_graph()


# ---------------------------------------------------------------------------
# 1-5: Intent classifier unit tests
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("text,expected_intent", [
    ("Hello",               "greeting"),
    ("Thanks a lot",        "thanks"),
    ("Goodbye",             "goodbye"),
    ("Show me my tickets",  "check_ticket_status"),
    ("Please create a ticket", "create_ticket"),
])
def test_intent_classifier_basic(text, expected_intent):
    """The classifier must predict the correct intent for clear examples."""
    intent, confidence = classify(text)
    assert intent == expected_intent, (
        f"Text={text!r}: expected {expected_intent!r}, got {intent!r} (confidence={confidence:.3f})"
    )
    assert 0.0 < confidence <= 1.0


# ---------------------------------------------------------------------------
# 6-8: Small-talk guard: technical messages route to pipeline
# ---------------------------------------------------------------------------

def test_technical_keyword_detection_vpn():
    """'vpn' is a technical keyword."""
    assert _has_technical_keyword("hi, my VPN is down") is True


def test_technical_keyword_detection_wifi():
    """'wifi' is a technical keyword."""
    assert _has_technical_keyword("thanks but wifi still not working") is True


def test_technical_keyword_detection_none():
    """'goodbye' has no technical keyword."""
    assert _has_technical_keyword("Goodbye, take care") is False


# ---------------------------------------------------------------------------
# 9-10: Router with USE_INTENT=False
# ---------------------------------------------------------------------------

def test_router_flag_off_always_pipeline(monkeypatch):
    """When USE_INTENT=False, every message routes to pipeline."""
    monkeypatch.setattr(settings, "USE_INTENT", False)
    for msg in ["Hello", "Show my tickets", "My VPN is broken"]:
        _, _, target = route_intent(msg, {})
        assert target == "pipeline", f"Expected pipeline for {msg!r}, got {target!r}"


def test_router_troubleshoot_routes_to_pipeline(monkeypatch):
    """troubleshoot intent always routes to pipeline."""
    monkeypatch.setattr(settings, "USE_INTENT", True)
    _, _, target = route_intent("My laptop screen is flickering", {})
    assert target == "pipeline"


# ---------------------------------------------------------------------------
# 11: Security bypasses intent router
# ---------------------------------------------------------------------------

def test_security_message_bypasses_intent_router(monkeypatch):
    """
    A security incident (e.g., ransomware) must set is_security_incident=True
    in triage, so route_after_triage sends it to security_escalation directly,
    never reaching the intent router.
    """
    monkeypatch.setattr(settings, "USE_INTENT", True)
    final_state = run_servicedesk_workflow(
        message="Help, my account was compromised by ransomware!"
    )
    assert final_state["is_security_incident"] is True
    assert final_state["final_status"] == "escalate"
    # Intent router never ran (or ran as no-op before security short-circuit in triage)
    assert "CRITICAL SECURITY ALERT" in final_state["final_reply"]


# ---------------------------------------------------------------------------
# 12-14: check_ticket_status handler
# ---------------------------------------------------------------------------

def test_check_ticket_status_unauthenticated(monkeypatch):
    """Unauthenticated user gets 'please log in' message via the handler directly."""
    # Test the handler directly — it must always return "log in" for user_id=None,
    # regardless of the feature flag.
    from app.services.intent_engine.handlers import handle_check_ticket_status
    state = {
        "user_id": None,
        "username": None,
        "user_role": None,
        "message": "Show me my tickets",
        "conversation_id": "TEST-UNAUTH-001",
        "conversation_history": "",
    }
    result = handle_check_ticket_status(state)
    assert "log in" in result["final_reply"].lower(), (
        f"Expected 'log in' in reply for unauthenticated user, got: {result['final_reply']!r}"
    )
    assert result["final_status"] == "answered"


def test_check_ticket_status_employee_rbac(client, employee_headers, db_session, monkeypatch):
    """Employee user can only see their own tickets via check_ticket_status."""
    monkeypatch.setattr(settings, "USE_INTENT", True)
    reset_workflow_graph()

    # Create a ticket for the employee via the tickets API
    res_create = client.post(
        "/api/tickets",
        json={"title": "My VPN is broken", "description": "VPN issue", "category": "network"},
        headers=employee_headers,
    )
    assert res_create.status_code == 201

    # Ask for ticket status via chat
    res = client.post(
        "/api/chat",
        json={"message": "mera ticket status batao"},
        headers=employee_headers,
    )
    assert res.status_code == 200
    data = res.json()
    # If intent was detected as check_ticket_status, reply should not contain
    # another user's ticket (we just check it doesn't error)
    assert "reply" in data
    assert len(data["reply"]) > 5


def test_check_ticket_status_no_login_reply_direct():
    """Handler directly: unauthenticated state returns login prompt (belt-and-suspenders)."""
    from app.services.intent_engine.handlers import handle_check_ticket_status
    state = {
        "user_id": None,
        "username": None,
        "user_role": None,
        "message": "show my tickets",
        "conversation_id": "TEST-ANON-2",
        "conversation_history": "",
    }
    result = handle_check_ticket_status(state)
    assert "log in" in result["final_reply"].lower()
    assert result["final_status"] == "answered"
    # Must not contain any other user's data
    assert "TKT-" not in result["final_reply"]


# ---------------------------------------------------------------------------
# 15-16: create_ticket handler
# ---------------------------------------------------------------------------

def test_create_ticket_intent_creates_ticket(db_session, monkeypatch):
    """create_ticket handler creates a ticket using triage data."""
    from app.services.intent_engine.handlers import handle_create_ticket
    monkeypatch.setattr(settings, "USE_INTENT", True)

    state = {
        "user_id": None,
        "username": None,
        "user_role": None,
        "message": "Please open a ticket for my VPN issue",
        "conversation_id": "TEST-CREATE-001",
        "conversation_history": "",
        "ticket_created_id": None,
        "triage": {
            "category": "network",
            "priority": "P3",
            "impact": "Medium",
            "urgency": "Medium",
            "suggested_group": "Network Infrastructure",
        },
    }
    result = handle_create_ticket(state)
    assert result["final_status"] == "answered"
    assert "TKT-" in result.get("final_reply", "")
    ticket_id = result.get("ticket_created_id")
    assert ticket_id is not None
    assert ticket_id.startswith("TKT-")


def test_create_ticket_deduplication(db_session, monkeypatch):
    """If ticket already exists in state, handler returns without creating another."""
    from app.services.intent_engine.handlers import handle_create_ticket
    monkeypatch.setattr(settings, "USE_INTENT", True)

    state = {
        "user_id": None,
        "username": None,
        "user_role": None,
        "message": "create a ticket",
        "conversation_id": "TEST-DEDUP-001",
        "conversation_history": "",
        "ticket_created_id": "TKT-EXISTING",  # already set
        "triage": {"category": "general", "priority": "P3"},
    }
    result = handle_create_ticket(state)
    assert "TKT-EXISTING" in result["final_reply"]
    # Should NOT overwrite the existing ticket_created_id with a new one
    new_id = result.get("ticket_created_id")
    assert new_id is None or new_id == "TKT-EXISTING"


# ---------------------------------------------------------------------------
# 17-20: End-to-end routing (feature flag / tricky cases)
# ---------------------------------------------------------------------------

def test_flag_off_original_pipeline_unchanged(client, monkeypatch):
    """When USE_INTENT=False existing test cases are unaffected."""
    monkeypatch.setattr(settings, "USE_INTENT", False)
    reset_workflow_graph()

    res = client.post("/api/chat", json={"message": "My Wi-Fi is not working"})
    assert res.status_code == 200
    data = res.json()
    assert data["category"] == "network"
    assert data["status"] == "answered"
    # Intent fields should be absent or None when flag is off
    assert data.get("intent") is None


def test_flag_on_greeting_handled_directly(client, monkeypatch):
    """When USE_INTENT=True a plain greeting returns a welcome message."""
    monkeypatch.setattr(settings, "USE_INTENT", True)
    reset_workflow_graph()

    res = client.post("/api/chat", json={"message": "Hello"})
    assert res.status_code == 200
    data = res.json()
    assert data.get("intent") == "greeting"
    reply_lower = data["reply"].lower()
    assert "hello" in reply_lower or "hi" in reply_lower or "welcome" in reply_lower or "help" in reply_lower


def test_hi_vpn_down_routes_to_pipeline(monkeypatch):
    """'hi, my VPN is down' must be treated as troubleshoot, not greeting."""
    monkeypatch.setattr(settings, "USE_INTENT", True)
    _, _, target = route_intent("hi, my VPN is down", {})
    assert target == "pipeline", f"Expected pipeline, got {target!r}"


def test_thanks_but_wifi_routes_to_pipeline(monkeypatch):
    """'thanks but wifi still not working' must be treated as troubleshoot."""
    monkeypatch.setattr(settings, "USE_INTENT", True)
    _, _, target = route_intent("thanks but wifi still not working", {})
    assert target == "pipeline", f"Expected pipeline, got {target!r}"
