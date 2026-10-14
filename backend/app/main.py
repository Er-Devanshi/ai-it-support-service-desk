"""
ServiceDesk-AI — Main FastAPI application entry point.

Autonomous Multi-Agent Assistant for Enterprise IT Operations.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.db.init_db import init_database
from app.routes import health, chat, auth, tickets, approvals, actions, audit
from app.utils.logger import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for database initialization and startup checks."""
    logger.info("Starting ServiceDesk-AI backend...")
    init_database()
    yield
    logger.info("Shutting down ServiceDesk-AI backend.")


app = FastAPI(
    title="ServiceDesk-AI",
    description=(
        "Autonomous Multi-Agent AI Assistant for Enterprise IT Operations. "
        "Provides conversational support, AI triage & prioritization, LangGraph orchestration, "
        "RAG integration contracts, simulated IT actions, human-in-the-loop approvals, and RBAC."
    ),
    version="0.2.0",
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# CORS Configuration
# ---------------------------------------------------------------------------
allow_origins = ["*"] if settings.ALLOW_ALL_ORIGINS else settings.CORS_ORIGINS

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Routers Registration
# ---------------------------------------------------------------------------
app.include_router(health.router, prefix="/api")
app.include_router(chat.router, prefix="/api")
app.include_router(auth.router, prefix="/api")
app.include_router(tickets.router, prefix="/api")
app.include_router(approvals.router, prefix="/api")
app.include_router(actions.router, prefix="/api")
app.include_router(audit.router, prefix="/api")
