"""
Health-check route.

GET /api/health
Returns the current running status and diagnostics of the service.
"""

from fastapi import APIRouter
from app.config import settings
from app.services.llm.factory import get_llm_provider

router = APIRouter(tags=["Health"])


@router.get("/health")
def health_check():
    """
    Liveness and readiness probe.
    Preserves exact Phase 1 keys ('status', 'service', 'phase')
    while exposing system diagnostics.
    """
    # Check active LLM provider descriptor
    provider_name = settings.LLM_PROVIDER
    is_mock = settings.DEMO_MODE or not bool(settings.GEMINI_API_KEY)
    
    return {
        "status": "running",
        "service": "ServiceDesk-AI",
        "version": "0.2.0",
        "phase": "Phase 2 — Autonomous Multi-Agent",
        "llm_provider": provider_name,
        "llm_model": settings.LLM_MODEL,
        "mode": "mock/demo" if is_mock else "live",
        "rag_enabled": settings.RAG_ENABLED,
    }
