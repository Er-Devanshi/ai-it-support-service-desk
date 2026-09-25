"""
ServiceDesk-AI — Main FastAPI application entry point.

Phase 1: Foundation only.
LLM integration, RAG, and multi-agent orchestration are planned for future phases.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import health, chat

# ---------------------------------------------------------------------------
# App initialisation
# ---------------------------------------------------------------------------

app = FastAPI(
    title="ServiceDesk-AI",
    description="AI-powered IT Support Desk — Phase 1 Foundation",
    version="0.1.0",
)

# ---------------------------------------------------------------------------
# CORS — allow the local frontend (file:// or localhost) to call the API.
# In production this should be locked down to specific origins.
# ---------------------------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # TODO (Phase 2+): restrict to your frontend origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------

app.include_router(health.router, prefix="/api")
app.include_router(chat.router,   prefix="/api")
