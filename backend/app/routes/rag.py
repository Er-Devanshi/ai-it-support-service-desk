from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.models.orm import User, UserRole
from app.services.auth_service import require_roles
from app.services.rag.ingest import ingest_knowledge_base
from app.services.nlp.retriever import BM25Retriever
from app.config import settings

router = APIRouter(prefix="/rag", tags=["RAG & Knowledge Base"])


class IngestRequest(BaseModel):
    reset: bool = Field(default=False, description="Whether to clear existing index before re-ingesting")
    directory: Optional[str] = Field(default=None, description="Optional custom directory path to ingest")


class IngestResponse(BaseModel):
    status: str
    documents_loaded: int
    chunks_indexed: int
    total_in_db: int
    index_dir: str
    retriever_type: str
    info: str


@router.get("/status")
def get_rag_status() -> Dict[str, Any]:
    """Return RAG pipeline status and BM25 index diagnostics."""
    if not settings.RAG_ENABLED:
        return {
            "rag_enabled": False,
            "status": "disabled",
            "message": "RAG pipeline is disabled via configuration.",
        }

    try:
        retriever = BM25Retriever()
        if retriever.index.total_docs == 0:
            return {
                "rag_enabled": True,
                "status": "empty",
                "message": "BM25 index exists but contains no documents",
                "total_docs": 0,
            }
        return {
            "rag_enabled": True,
            "status": "ready",
            "retriever": "BM25 (in-house)",
            "total_docs": retriever.index.total_docs,
            "vocab_size": retriever.index.vocab_size,
            "avg_doc_length": round(retriever.index.avg_doc_length, 2),
        }
    except Exception as e:
        return {
            "rag_enabled": True,
            "status": "error",
            "message": str(e),
        }


@router.post("/ingest", response_model=IngestResponse)
def trigger_ingestion(
    req: IngestRequest,
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.SUPPORT_AGENT])),
):
    """
    Ingest or re-index knowledge base documents into BM25 index.
    Protected endpoint: requires 'admin' or 'support_agent' role.
    """
    try:
        from pathlib import Path
        dir_path = Path(req.directory) if req.directory else None
        res = ingest_knowledge_base(directory=dir_path, reset=req.reset)
        if res.get("status") == "warning":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=res.get("message", "No documents found to ingest."),
            )
        return IngestResponse(**res)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Knowledge base ingestion failed: {e}",
        )
