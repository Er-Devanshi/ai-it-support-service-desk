"""
Tests for AI Ticket Triage, Security Incident Rules, and LangGraph Workflow Routing.
"""

import pytest
from app.services.triage_service import TicketTriageService, calculate_priority, TriageResult
from app.models.orm import TicketPriority
from app.services.workflow.graph import run_servicedesk_workflow, get_workflow_graph
from app.services.workflow.state import ServiceDeskState


def test_priority_matrix_calculation():
    """Test 14: Verify ITIL priority calculation matrix."""
    assert calculate_priority("High", "High") == TicketPriority.P1
    assert calculate_priority("High", "Medium") == TicketPriority.P2
    assert calculate_priority("Medium", "High") == TicketPriority.P2
    assert calculate_priority("Medium", "Medium") == TicketPriority.P3
    assert calculate_priority("Low", "High") == TicketPriority.P3
    assert calculate_priority("Low", "Low") == TicketPriority.P4


def test_security_incident_deterministic_escalation():
    """Test 11 & 22: Suspicious compromise or ransomware automatically escalates to P1."""
    triage_service = TicketTriageService()
    res = triage_service.triage_message("Our servers are infected with ransomware and files are encrypted!")
    
    assert res.category == "security"
    assert res.priority == TicketPriority.P1
    assert res.escalation_required is True
    assert res.suggested_group == "Security Operations"
    assert "security incident" in res.escalation_reason.lower()


def test_phishing_escalation():
    """Test 22b: Phishing alert escalates to security team."""
    triage_service = TicketTriageService()
    res = triage_service.triage_message("I clicked a suspicious phishing link asking for my login password.")
    assert res.category == "security"
    assert res.escalation_required is True


def test_langgraph_security_routing():
    """Test 15: Security alert routes to security escalation and issues SecOps instructions."""
    final_state = run_servicedesk_workflow(
        message="Help, my account has been compromised by an unauthorized attacker!"
    )
    assert final_state["is_security_incident"] is True
    assert final_state["final_status"] == "escalate"
    assert "CRITICAL SECURITY ALERT" in final_state["final_reply"]
    assert "SecOps" in final_state["final_reply"]


def test_langgraph_action_routing_approval():
    """Test 15b: Requesting account unlock routes to action decision and requires approval."""
    final_state = run_servicedesk_workflow(
        message="Please unlock account for user employee"
    )
    assert final_state["approval_needed"] is True
    assert final_state["approval_id"] is not None
    assert final_state["final_status"] == "pending_approval"
    assert "Approval Required" in final_state["final_reply"]


def test_langgraph_loop_bounding_and_termination():
    """Test 16: Workflow terminates deterministically within iteration bounds."""
    graph = get_workflow_graph()
    initial_state: ServiceDeskState = {
        "message": "My Wi-Fi is slow",
        "conversation_id": "TEST-LOOP-001",
        "user_id": None,
        "username": None,
        "user_role": None,
        "triage": {},
        "is_security_incident": False,
        "conversation_history": "",
        "retrieved_docs": [],
        "citations": [],
        "action_requested": None,
        "action_result": None,
        "approval_needed": False,
        "approval_id": None,
        "escalation_needed": False,
        "escalation_reason": None,
        "ticket_created_id": None,
        "final_reply": "",
        "final_status": "answered",
        "note": "",
        "mode": "mock",
        "iteration_count": 0,
        "is_terminal": False,
    }

    result = graph.invoke(initial_state)
    assert result["is_terminal"] is True
    assert result["iteration_count"] >= 1
    assert result["iteration_count"] <= 5
