"""
Health-check route.

GET /api/health
Returns the current running status and diagnostics of the service.
"""

from fastapi import APIRouter

router = APIRouter(tags=["Health"])


@router.get("/health")
def health_check():
    """
    Liveness and readiness probe.
    Reports in-house NLP engine instead of external LLM providers.
    """
    return {
        "status": "running",
        "service": "ServiceDesk-AI",
        "version": "0.2.0",
        "phase": "Phase 2 — Autonomous Multi-Agent",
        "engine": "in-house_nlp",
        "engine_type": "Naive Bayes + BM25",
        "mode": "own_engine",
        "rag_enabled": True,
        "rag_provider": "BM25 (in-house)",
    }
