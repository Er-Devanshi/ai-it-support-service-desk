"""
Chat route.

POST /api/chat
Accepts a user message and returns a structured response from the
autonomous multi-agent orchestration workflow.
"""

from typing import Optional
from fastapi import APIRouter, Depends
from app.models.chat import ChatRequest, ChatResponse
from app.models.orm import User
from app.services.chat_service import process_message
from app.services.auth_service import get_current_user_optional

router = APIRouter(tags=["Chat"])


@router.post("/chat", response_model=ChatResponse)
def chat(
    request: ChatRequest,
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """
    Receive a user message and return an AI-guided IT support response.

    Request body:
        { "message": "My Wi-Fi is not working", "conversation_id": "optional-id" }

    Response body:
        {
            "reply": "...",
            "category": "network",
            "status": "answered",
            "note": "...",
            "conversation_id": "...",
            "priority": "P3",
            "ticket_id": null,
            "escalated": false,
            "requires_approval": false,
            "approval_id": null,
            "citations": [...]
        }
    """
    return process_message(
        message=request.message,
        conversation_id=request.conversation_id,
        user=current_user,
    )
