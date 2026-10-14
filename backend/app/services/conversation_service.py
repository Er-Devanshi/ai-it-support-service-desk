"""
Conversation history persistence for ServiceDesk-AI.

Stores user and assistant messages per conversation_id in SQLite.
Context is retrieved and passed to the LLM on subsequent turns,
giving the system basic multi-turn memory without an external store.

Limitations:
- History is loaded per-request (no streaming or real-time push).
- No summarisation yet — older turns are truncated by MAX_HISTORY_TURNS.
- Conversation ownership check: if a user is authenticated their user_id
  is recorded; anonymous requests are only matched by conversation_id.
"""

from typing import Optional, List
from sqlalchemy.orm import Session

from app.models.orm import ConversationMessage
from app.utils.logger import logger

# Maximum number of prior turns loaded into LLM context per request.
# Each "turn" is one user message + one assistant reply (2 rows).
MAX_HISTORY_TURNS = 6   # = up to 12 rows


def save_message(
    db: Session,
    conversation_id: str,
    role: str,               # "user" | "assistant"
    content: str,
    user_id: Optional[int] = None,
) -> ConversationMessage:
    """Persist a single conversation message."""
    msg = ConversationMessage(
        conversation_id=conversation_id,
        user_id=user_id,
        role=role,
        content=content,
    )
    db.add(msg)
    try:
        db.commit()
        db.refresh(msg)
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to save conversation message: {e}")
    return msg


def get_history(
    db: Session,
    conversation_id: str,
    max_turns: int = MAX_HISTORY_TURNS,
) -> List[ConversationMessage]:
    """
    Return the most-recent messages for a conversation, oldest-first,
    limited to max_turns * 2 rows (user + assistant alternating).
    """
    rows = (
        db.query(ConversationMessage)
        .filter(ConversationMessage.conversation_id == conversation_id)
        .order_by(ConversationMessage.created_at.desc())
        .limit(max_turns * 2)
        .all()
    )
    return list(reversed(rows))


def format_history_for_llm(messages: List[ConversationMessage]) -> str:
    """
    Render prior turns as a compact text block suitable for injecting
    into an LLM system or user prompt.
    """
    if not messages:
        return ""
    lines = ["--- Previous conversation context ---"]
    for m in messages:
        speaker = "User" if m.role == "user" else "Assistant"
        lines.append(f"{speaker}: {m.content}")
    lines.append("--- End of context ---")
    return "\n".join(lines)
