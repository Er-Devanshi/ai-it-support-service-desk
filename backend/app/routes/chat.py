"""
Chat route.

POST /api/chat
Accepts a user message and returns a structured response.

Phase 1: No LLM is connected yet. The chat service returns a rule-based
placeholder response so the frontend ↔ backend communication works end-to-end.
LLM / RAG integration is planned for Phase 2.
"""

from fastapi import APIRouter
from app.models.chat import ChatRequest, ChatResponse
from app.services.chat_service import process_message

router = APIRouter(tags=["Chat"])


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    """
    Receive a user message and return an IT support response.

    Request body:
        { "message": "My Wi-Fi is not working" }

    Response body:
        {
            "reply": "...",
            "category": "...",
            "status": "...",
            "note": "..."
        }
    """
    return process_message(request.message)
