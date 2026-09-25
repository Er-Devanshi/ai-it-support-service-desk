"""
Health-check route.

GET /api/health
Returns the current running status of the service.
"""

from fastapi import APIRouter

router = APIRouter(tags=["Health"])


@router.get("/health")
def health_check():
    """
    Simple liveness probe.
    Useful for confirming the backend is up before making other API calls.
    """
    return {
        "status": "running",
        "service": "ServiceDesk-AI",
        "version": "0.1.0",
        "phase": "Phase 1 — Foundation",
    }
