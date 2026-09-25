"""
Pydantic models for the chat endpoint.

These define the shape of the request and response JSON bodies.
Using Pydantic ensures automatic validation and clear API documentation
in the FastAPI /docs interface.
"""

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Body expected by POST /api/chat."""

    message: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="The user's IT support question or problem description.",
        examples=["My Wi-Fi is not working"],
    )


class ChatResponse(BaseModel):
    """Body returned by POST /api/chat."""

    reply: str = Field(description="The support response text shown to the user.")
    category: str = Field(description="Detected IT issue category (e.g. 'network', 'account').")
    status: str = Field(description="Handling status: 'answered' | 'escalate' | 'unknown'.")
    note: str = Field(description="Internal note, e.g. phase limitation reminder.")
